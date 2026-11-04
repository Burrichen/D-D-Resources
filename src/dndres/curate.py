"""Curation helpers: status, duplicate detection, validation, index build."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import jsonschema
from rapidfuzz import fuzz, process

from .common import (CONTENT, INDEX, RAW, REVIEW, ROOT, TYPE_DIRS, _jsonable, iter_content,
                     iter_raw, load_sources, now_iso)

STUB_CHARS = 120
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
MDLINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
CODEBLOCK_RE = re.compile(r"```.*?```", re.S)
TITLE_NOISE_RE = re.compile(r"\((name pending|wip|draft|old|copy|new|tbd)\)|\b(copy|old|v\d+)\b", re.I)


def _curated_refs() -> dict[tuple[str, str], tuple[str, str]]:
    """(source, raw path) -> (content entry id, hash at merge time)."""
    refs = {}
    for path, fm, _ in iter_content():
        for s in fm.get("sources", []) or []:
            refs[(s.get("source"), s.get("path"))] = (fm.get("id", str(path)), s.get("hash"))
    return refs


def _plain(body: str) -> str:
    body = CODEBLOCK_RE.sub(" ", body)
    body = WIKILINK_RE.sub(lambda m: m.group(2) or m.group(1), body)
    body = MDLINK_RE.sub(lambda m: m.group(1), body)
    body = re.sub(r"<!--.*?-->|%%.*?%%", " ", body, flags=re.S)
    body = re.sub(r"[#>*_`|\-\[\]!]+", " ", body)
    return re.sub(r"\s+", " ", body).strip().lower()


def _norm_title(t: str) -> str:
    t = TITLE_NOISE_RE.sub(" ", t)
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


# ---------------- status ----------------

def status(verbose: bool = False) -> None:
    refs = _curated_refs()
    seen = set()
    per_source = defaultdict(Counter)
    stale, uncurated = [], []
    for src, rel, fm, body in iter_raw():
        seen.add((src, rel))
        key = (src, rel)
        if key in refs:
            if refs[key][1] != fm.get("_content_hash"):
                stale.append((refs[key][0], src, rel))
                per_source[src]["stale"] += 1
            else:
                per_source[src]["curated"] += 1
        else:
            uncurated.append((src, rel, len(_plain(body))))
            per_source[src]["uncurated"] += 1
    orphans = [(cid, s, p) for (s, p), (cid, _) in refs.items() if (s, p) not in seen]

    print(f"{'source':28} {'uncurated':>9} {'curated':>8} {'stale':>6}")
    for src in sorted(per_source):
        c = per_source[src]
        print(f"{src:28} {c['uncurated']:>9} {c['curated']:>8} {c['stale']:>6}")
    n_content = sum(1 for _ in iter_content())
    print(f"\ncontent entries: {n_content}   stale: {len(stale)}   orphaned source refs: {len(orphans)}")
    for cid, s, p in stale:
        print(f"  STALE   {cid}  <- {s}:{p} changed since merge")
    for cid, s, p in orphans:
        print(f"  ORPHAN  {cid}  <- {s}:{p} no longer exists in raw/")
    if verbose:
        for s, p, n in uncurated:
            print(f"  todo  {s}:{p}  ({n} chars)")


# ---------------- duplicates ----------------

class _DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def _boilerplate_lines(bodies: list[str], min_files: int = 4) -> set[str]:
    """Lines that recur across many notes (template headings, infobox scaffolding)."""
    c = Counter()
    for b in bodies:
        c.update({ln.strip() for ln in b.splitlines() if ln.strip()})
    return {ln for ln, n in c.items() if n >= min_files}


def _strip_boilerplate(body: str, boiler: set[str]) -> str:
    return "\n".join(ln for ln in body.splitlines() if ln.strip() not in boiler)


def _numbered_siblings(a: str, b: str) -> bool:
    """'session 2' vs 'session 6', 'quote1' vs 'quote10', 'd100 varient' vs '2d6 varient'."""
    return a != b and re.sub(r"\d+", "#", a) == re.sub(r"\d+", "#", b)


def dupes(title_threshold: int = 90, body_threshold: int = 80) -> None:
    raw_rows = list(iter_raw())
    content_rows = list(iter_content())
    boiler = _boilerplate_lines([b for *_, b in raw_rows] + [b for *_, b in content_rows])
    items = []  # dicts: key, title, names, text
    for src, rel, fm, body in raw_rows:
        body = _strip_boilerplate(body, boiler)
        title = str(fm.get("_title") or Path(rel).stem)
        names = {title}
        for k in ("aliases", "Aliases", "alias", "Alias"):
            v = fm.get(k)
            names.update([v] if isinstance(v, str) else (v or []))
        items.append({"key": f"{src}:{rel}", "title": title,
                      "names": {_norm_title(str(n)) for n in names if n} - {""},
                      "text": _plain(body), "hash": fm.get("_content_hash")})
    for path, fm, body in content_rows:
        body = _strip_boilerplate(body, boiler)
        names = {fm.get("name", "")} | set(fm.get("aliases", []) or [])
        items.append({"key": f"content:{fm.get('id', path)}", "title": fm.get("name", ""),
                      "names": {_norm_title(str(n)) for n in names if n} - {""},
                      "text": _plain(body), "hash": None})

    n = len(items)
    dsu = _DSU(n)
    reasons: dict[frozenset, str] = {}

    # 1. exact normalised-name matches (incl. aliases)
    by_name = defaultdict(list)
    for i, it in enumerate(items):
        for nm in it["names"]:
            by_name[nm].append(i)
    for nm, idx in by_name.items():
        for j in idx[1:]:
            dsu.union(idx[0], j)
            reasons.setdefault(frozenset((idx[0], j)), f"same name '{nm}'")

    # 2. fuzzy title matches
    titles = [_norm_title(it["title"]) for it in items]
    m = process.cdist(titles, titles, scorer=fuzz.token_sort_ratio, score_cutoff=title_threshold, workers=-1)
    for i in range(n):
        for j in range(i + 1, n):
            if (m[i][j] and len(titles[i]) > 3 and len(titles[j]) > 3
                    and not _numbered_siblings(titles[i], titles[j])):
                dsu.union(i, j)
                reasons.setdefault(frozenset((i, j)), f"similar titles ({int(m[i][j])}%)")

    # 3. body similarity (ignores stubs)
    long_idx = [i for i in range(n) if len(items[i]["text"]) >= STUB_CHARS * 2]
    bodies = [items[i]["text"][:4000] for i in long_idx]
    if bodies:
        m = process.cdist(bodies, bodies, scorer=fuzz.token_sort_ratio, score_cutoff=body_threshold, workers=-1)
        for a in range(len(long_idx)):
            for b in range(a + 1, len(long_idx)):
                if m[a][b]:
                    i, j = long_idx[a], long_idx[b]
                    dsu.union(i, j)
                    reasons.setdefault(frozenset((i, j)), f"similar text ({int(m[a][b])}%)")

    groups = defaultdict(list)
    for i in range(n):
        groups[dsu.find(i)].append(i)
    groups = [g for g in groups.values() if len(g) > 1]

    # identical-content groups are trivially mergeable; flag them
    out = []
    for g in groups:
        members = [items[i] for i in g]
        texts = {it["text"] for it in members}
        out.append({
            "members": [it["key"] for it in members],
            "identical_text": len(texts) == 1 and len(next(iter(texts))) >= STUB_CHARS,
            "all_stubs": all(len(it["text"]) < STUB_CHARS for it in members),
            "has_content_entry": any(it["key"].startswith("content:") for it in members),
            "reasons": sorted({r for pair, r in reasons.items() if pair <= set(g)}),
            "sizes": {it["key"]: len(it["text"]) for it in members},
        })
    out.sort(key=lambda g: (g["has_content_entry"], not g["identical_text"], -len(g["members"])))

    stubs = sorted(it["key"] for it in items if len(it["text"]) < STUB_CHARS and not it["key"].startswith("content:"))

    REVIEW.mkdir(exist_ok=True)
    (REVIEW / "duplicates.json").write_text(json.dumps({"generated": now_iso(), "groups": out,
                                                        "stubs": stubs}, indent=1))
    lines = ["# Duplicate candidates", "",
             f"_Generated {now_iso()} by `uv run dndres dupes`. Do not edit — regenerate._", "",
             f"{len(out)} groups · {sum(g['identical_text'] for g in out)} with identical text · "
             f"{len(stubs)} stub/empty notes", ""]
    for k, g in enumerate(out, 1):
        flag = ("IDENTICAL" if g["identical_text"] else "has canonical" if g["has_content_entry"]
                else "all stubs" if g["all_stubs"] else "review")
        lines.append(f"## {k}. [{flag}] " + Path(g["members"][0].split(":", 1)[1]).stem)
        lines.append("Why: " + "; ".join(g["reasons"]))
        for mbr in g["members"]:
            lines.append(f"- `{mbr}` ({g['sizes'][mbr]} chars)")
        lines.append("")
    lines += ["## Stubs / near-empty notes", "",
              "These are under %d characters of text. Usually: discard, or fold into a parent entry." % STUB_CHARS, ""]
    lines += [f"- `{s}`" for s in stubs]
    (REVIEW / "duplicates.md").write_text("\n".join(lines) + "\n")
    print(f"{len(out)} duplicate groups ({sum(g['identical_text'] for g in out)} identical), "
          f"{len(stubs)} stubs -> review/duplicates.md")


# ---------------- validate ----------------

def validate() -> int:
    schema = json.loads((ROOT / "schemas" / "entry.schema.json").read_text())
    source_ids = {s["id"] for s in load_sources()}
    errors: list[str] = []
    ids: dict[str, Path] = {}
    entries = list(iter_content())
    for path, fm, body in entries:
        rel = path.relative_to(ROOT)
        try:
            jsonschema.validate(_jsonable(fm), schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{rel}: schema: {e.message} at {'/'.join(map(str, e.path)) or '(root)'}")
            continue
        cid = fm["id"]
        t, slug = cid.split("/", 1)
        if t != fm["type"]:
            errors.append(f"{rel}: id prefix '{t}' != type '{fm['type']}'")
        expected = CONTENT / TYPE_DIRS[fm["type"]] / f"{slug}.md"
        if path != expected:
            errors.append(f"{rel}: should live at {expected.relative_to(ROOT)}")
        if cid in ids:
            errors.append(f"{rel}: duplicate id {cid} (also {ids[cid].relative_to(ROOT)})")
        ids[cid] = path
        for s in fm["sources"]:
            if s["source"] not in source_ids:
                errors.append(f"{rel}: unknown source '{s['source']}'")
            elif not (RAW / s["source"] / s["path"]).exists():
                errors.append(f"{rel}: raw file missing {s['source']}:{s['path']}")
        for wl in WIKILINK_RE.findall(CODEBLOCK_RE.sub("", body)):
            errors.append(f"{rel}: unresolved wikilink [[{wl[0]}]] (convert to a markdown link)")
        for _, href in MDLINK_RE.findall(body):
            if href.startswith(("/content/", "../", "./")) and href.endswith(".md"):
                target = (ROOT / href.lstrip("/")) if href.startswith("/") else (path.parent / href)
                if not target.resolve().exists():
                    errors.append(f"{rel}: broken link {href}")
            elif href.startswith("/assets/") and not (ROOT / href.lstrip("/").replace("%20", " ")).exists():
                errors.append(f"{rel}: missing asset {href}")
    for path, fm, _ in entries:
        for r in fm.get("related", []) or []:
            if r not in ids:
                errors.append(f"{path.relative_to(ROOT)}: related id '{r}' does not exist")
    for e in errors:
        print(e)
    print(f"{len(entries)} entries checked, {len(errors)} problems")
    return 1 if errors else 0


# ---------------- index ----------------

def build_index() -> None:
    INDEX.mkdir(exist_ok=True)
    entries, aliases = [], {}
    with (INDEX / "entries.jsonl").open("w") as fh:
        for path, fm, body in iter_content():
            fm = _jsonable(fm)
            rec = {k: fm.get(k) for k in ("id", "type", "name", "aliases", "summary", "setting",
                                          "tags", "related", "status", "updated", "images")}
            rec["path"] = str(path.relative_to(ROOT))
            rec["fields"] = {k: v for k, v in fm.items() if k not in rec and k not in ("sources",)}
            entries.append(rec)
            fh.write(json.dumps({**rec, "body": body.strip()}, ensure_ascii=False) + "\n")
            for a in [fm.get("name")] + (fm.get("aliases") or []):
                if a:
                    aliases.setdefault(a.lower(), fm["id"])
    manifest = {
        "generated": now_iso(),
        "count": len(entries),
        "by_type": dict(Counter(e["type"] for e in entries)),
        "aliases": dict(sorted(aliases.items())),
        "entries": entries,
    }
    (INDEX / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"index/manifest.json + index/entries.jsonl: {len(entries)} entries")
