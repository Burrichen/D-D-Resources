"""`dndres review`: a local web UI for working through review/duplicates.md and review/conflicts.md.

The review/*.md files are the source of truth. Every request re-reads them, so whatever
`dndres dupes` (or Claude, via the curate skill) last wrote is what the UI shows. Saving an
item writes a canonical entry to content/, removes the item from its .md file, logs the
decision in review/decisions.md and rebuilds index/.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import secrets
import threading
import webbrowser
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import jsonschema
import yaml

from . import curate
from .common import (CONTENT, RAW, REVIEW, ROOT, TYPE_DIRS, _jsonable, iter_content, join_frontmatter,
                     load_sources, slugify, split_frontmatter, today)

UI_DIR = Path(__file__).with_name("review_ui")
DUP_MD = REVIEW / "duplicates.md"
DUP_JSON = REVIEW / "duplicates.json"
CONF_MD = REVIEW / "conflicts.md"

STANDARD_KEYS = ("id", "type", "name", "aliases", "summary", "setting", "tags", "related", "status",
                 "sources", "licence", "images", "updated")
UI_ONLY_KEYS = {"noteicon", "cover", "banner", "cssclasses", "cssclass", "tags", "tag",
                "aliases", "alias", "type", "status"}
DROP_FENCES = {"dataview", "dataviewjs", "ccard", "yaml:dbfolder", "dbfolder"}
CONFLICT_START, CONFLICT_SEP, CONFLICT_END = "<<<<<<<", "=======", ">>>>>>>"
REWRITE_RATIO = 0.35  # word-level similarity above which two differing passages count as rival versions
CONFLICT_LINE_RE = re.compile(r"^(<<<<<<<|>>>>>>>)( |$)|^=======$", re.M)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CALLOUT_RE = re.compile(r"^((?:\s*>)+)\s*\[!([\w-]+)\][+-]?\s*(.*)$")
EMPTY_LINK_RE = re.compile(r"^(?:[-*+]\s*)?\[\[\s*\]\]$")
ASSET_RE = re.compile(r"\]\((/assets/[^)\s]+)\)")
TYPE_HINTS = {
    "country": "location", "region": "location", "settlement": "location", "city": "location",
    "town": "location", "village": "location", "capital": "location", "location": "location",
    "landmark": "location", "magic-item": "item", "item": "item", "npc": "character",
    "character": "character", "god": "deity", "deity": "deity", "faction": "faction",
    "short-story": "story", "story": "story", "ancient creature": "creature", "creature": "creature",
    "race": "species", "species": "species", "spell": "spell",
}
PATH_HINTS = [
    ("deity", r"\bgods?\b|scions?|deit|pantheon"),
    ("campaign", r"sessions?|campaigns?"),
    ("table", r"\btables?\b|weather|\bd100\b|\b2d6\b"),
    ("mechanic", r"mechanics?|\brules?\b|homebrew"),
    ("character", r"characters?|\bnpcs?\b|\bpeople\b|\bpcs?\b"),
    ("faction", r"factions?|organi[sz]ations?|guilds?"),
    ("species", r"species|\braces?\b"),
    ("creature", r"creatures?|monsters?|bestiary"),
    ("item", r"\bitems?\b|artifacts?|equipment"),
    ("spell", r"\bspells?\b"),
    ("story", r"stor(y|ies)"),
    ("lore", r"timeline|\blore\b|cosmolog|histor"),
    ("location", r"locations?|\bworld\b|geograph|regions?|settlements?|cities|continent|planes?"),
]

_write_lock = threading.Lock()


class ReviewError(Exception):
    def __init__(self, message: str, details: list[str] | None = None, status: int = 400):
        super().__init__(message)
        self.details = details or []
        self.status = status


# ---------------------------------------------------------------- review/*.md parsing

def _hid(prefix: str, *parts) -> str:
    return prefix + hashlib.sha1("\n".join(map(str, parts)).encode()).hexdigest()[:12]


def _blocks(text: str) -> tuple[list[str], list[list[str]]]:
    """Split markdown into (header lines, [block lines...]) on '## ' headings."""
    header, blocks, cur = [], [], None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = [line]
            blocks.append(cur)
        elif cur is None:
            header.append(line)
        else:
            cur.append(line)
    return header, blocks


_DUP_HEAD_RE = re.compile(r"^## (\d+)\. \[([^\]]+)\] (.*)$")
_DUP_MEMBER_RE = re.compile(r"^- `([^`]+)`(?: \((\d+) chars\))?")


def _parse_dup_block(block: list[str]) -> dict | None:
    m = _DUP_HEAD_RE.match(block[0])
    if not m:
        return None
    item = {"kind": "duplicate", "number": int(m[1]), "flag": m[2], "title": m[3].strip(),
            "reasons": [], "members": [], "sizes": {}}
    for line in block[1:]:
        if line.startswith("Why:"):
            item["reasons"] = [r.strip() for r in line[4:].split(";") if r.strip()]
        elif mm := _DUP_MEMBER_RE.match(line):
            item["members"].append(mm[1])
            if mm[2]:
                item["sizes"][mm[1]] = int(mm[2])
    item["id"] = _hid("d-", *sorted(item["members"]))
    return item


def parse_duplicates() -> dict:
    if not DUP_MD.exists():
        return {"items": [], "generated": None, "stubs": 0}
    header, blocks = _blocks(DUP_MD.read_text())
    items = [it for b in blocks if (it := _parse_dup_block(b)) and len(it["members"]) > 1]
    gen = next((m[1] for ln in header if (m := re.search(r"_Generated (\S+)", ln))), None)
    stubs = next((len([ln for ln in b if ln.startswith("- `")]) for b in blocks
                  if b[0].startswith("## Stubs")), 0)
    return {"items": items, "generated": gen, "stubs": stubs}


def _parse_conflict_block(block: list[str]) -> dict:
    title = block[0][3:].strip()
    entry, members, claims, notes = None, [], {}, []
    for line in block[1:]:
        s = line.strip()
        if m := re.match(r"^[-*]\s*Entry:\s*`([^`]+)`", s):
            entry = m[1].removeprefix("content:")
        elif m := re.match(r"^[-*]\s*`([^`]+)`\s*:?\s*(.*)$", s):
            members.append(m[1])
            if m[2]:
                claims[m[1]] = m[2]
        elif s:
            notes.append(s)
    if entry is None and ":" not in title.split()[0]:
        cand = title.split(":")[0].strip().split()[0]
        if re.fullmatch(r"[a-z-]+/[a-z0-9-]+", cand):
            entry = cand
    keys = ([f"content:{entry}"] if entry else []) + [k for k in members if k != f"content:{entry}"]
    return {"kind": "conflict", "title": title, "entry": entry, "members": keys, "claims": claims,
            "notes": notes, "reasons": [], "flag": "conflict",
            "id": _hid("c-", title, *keys)}


def parse_conflicts() -> list[dict]:
    if not CONF_MD.exists():
        return []
    _, blocks = _blocks(CONF_MD.read_text())
    return [_parse_conflict_block(b) for b in blocks]


def find_item(item_id: str) -> dict:
    for it in parse_duplicates()["items"] + parse_conflicts():
        if it["id"] == item_id:
            return it
    raise ReviewError("This item is no longer in review/duplicates.md or review/conflicts.md "
                      "(it may have been resolved or the file regenerated).", status=404)


def remove_duplicate(item_id: str) -> None:
    header, blocks = _blocks(DUP_MD.read_text())
    kept, removed_members = [], None
    for b in blocks:
        it = _parse_dup_block(b)
        if it and it["id"] == item_id:
            removed_members = sorted(it["members"])
            continue
        kept.append(b)
    if removed_members is None:
        raise ReviewError("Group not found in review/duplicates.md", status=404)
    n, n_ident = 0, 0
    for b in kept:
        if m := _DUP_HEAD_RE.match(b[0]):
            n += 1
            n_ident += m[2] == "IDENTICAL"
            b[0] = f"## {n}. [{m[2]}] {m[3]}"
    header = [re.sub(r"^\d+ groups · \d+ with identical text", f"{n} groups · {n_ident} with identical text", ln)
              for ln in header]
    DUP_MD.write_text("\n".join(header + [ln for b in kept for ln in b]).rstrip("\n") + "\n")
    if DUP_JSON.exists():
        data = json.loads(DUP_JSON.read_text())
        data["groups"] = [g for g in data.get("groups", []) if sorted(g["members"]) != removed_members]
        DUP_JSON.write_text(json.dumps(data, indent=1))


def remove_conflict(item_id: str) -> None:
    header, blocks = _blocks(CONF_MD.read_text())
    kept = [b for b in blocks if _parse_conflict_block(b)["id"] != item_id]
    if len(kept) == len(blocks):
        raise ReviewError("Conflict not found in review/conflicts.md", status=404)
    if not kept and not any("_None yet._" in ln for ln in header):
        header = [*header, "_None yet._"] if header[-1:] == [""] else [*header, "", "_None yet._"]
    CONF_MD.write_text("\n".join(header + [ln for b in kept for ln in b]).rstrip("\n") + "\n")


# ---------------------------------------------------------------- members

def _short_label(source: str) -> str:
    m = re.search(r"-(v\d+)$", source, re.I)
    return m[1] if m else source


def _content_path(cid: str) -> Path | None:
    t, _, slug = cid.partition("/")
    if t in TYPE_DIRS and slug:
        p = CONTENT / TYPE_DIRS[t] / f"{slug}.md"
        if p.exists():
            return p
    for p, fm, _ in iter_content():
        if fm.get("id") == cid:
            return p
    return None


def load_member(key: str) -> dict:
    if key.startswith("content:"):
        cid = key.removeprefix("content:")
        p = _content_path(cid)
        fm, body = split_frontmatter(p.read_text()) if p else ({}, "")
        return {"key": key, "kind": "entry", "source": "content", "path": str(p.relative_to(ROOT)) if p else cid,
                "title": fm.get("name", cid), "label": "entry", "exists": p is not None,
                "fm": _jsonable(fm), "body": body, "hash": None, "licence": fm.get("licence")}
    src, _, rel = key.partition(":")
    p = (RAW / src / rel)
    ok = p.resolve().is_relative_to(RAW.resolve()) and p.is_file()
    fm, body = split_frontmatter(p.read_text()) if ok else ({}, "")
    return {"key": key, "kind": "raw", "source": src, "path": rel, "label": _short_label(src),
            "title": str(fm.get("_title") or Path(rel).stem), "exists": ok,
            "fm": _jsonable({k: v for k, v in fm.items() if not str(k).startswith("_")}),
            "body": body, "hash": fm.get("_content_hash"), "licence": fm.get("_licence")}


# ---------------------------------------------------------------- preparing bodies

_template_cache: dict[str, set[str]] = {}


def template_lines(source_id: str) -> set[str]:
    """Stripped lines from the source vault's Obsidian templates (read-only), used to spot scaffolding."""
    if source_id in _template_cache:
        return _template_cache[source_id]
    lines: set[str] = set()
    src = next((s for s in load_sources() if s["id"] == source_id), None)
    if src and src.get("type") == "obsidian" and src.get("path"):
        base = Path(src["path"]).expanduser()
        for pat in src.get("skip", []) or []:
            if "templat" not in pat.lower():
                continue
            files = (base / pat[:-3]).rglob("*.md") if pat.endswith("/**") else base.glob(pat)
            for f in files:
                try:
                    _, body = split_frontmatter(f.read_text(errors="ignore"))
                except OSError:
                    continue
                lines.update(ln.strip() for ln in body.splitlines())
    lines -= {"", "---", ">", "-"}
    lines = {ln for ln in lines if not HEADING_RE.match(ln)}
    _template_cache[source_id] = lines
    return lines


def link_map() -> dict[str, tuple[str, str]]:
    """lower-cased name / alias / cited raw title -> (entry id, repo-relative path)."""
    out: dict[str, tuple[str, str]] = {}
    for p, fm, _ in iter_content():
        if not fm.get("id"):
            continue
        val = (fm["id"], str(p.relative_to(ROOT)))
        names = [fm.get("name")] + list(fm.get("aliases") or [])
        names += [Path(s.get("path", "")).stem for s in fm.get("sources") or []]
        for n in names:
            if n:
                out.setdefault(str(n).strip().lower(), val)
    return out


def prepare(body: str, name: str, source: str, strip: bool, links: dict) -> tuple[str, list[str]]:
    """Convert Obsidian-flavoured markdown into content/ markdown (see the curate skill)."""
    gm_notes: list[str] = []

    def take_gm(m: re.Match) -> str:
        if m[1].strip():
            gm_notes.append(m[1].strip())
        return ""

    body = re.sub(r"%%(.*?)%%", take_gm, body, flags=re.S)
    tmpl = template_lines(source) if strip else set()
    refs: list[str] = []

    def link_sub(m: re.Match) -> str:
        target = m[1].strip()
        text = (m[2] or Path(target).name).strip()
        hit = links.get(Path(target).name.lower()) or links.get(target.lower())
        if hit:
            return f"[{text}](/{hit[1]})"
        if target not in refs:
            refs.append(target)
        return text

    out: list[str] = []
    fence: str | None = None
    dropping = False
    for line in body.splitlines():
        s = line.strip()
        if fence is None and (fm := re.match(r"^(```+|~~~+)\s*([\w:+-]*)", s)):
            fence = fm[1]
            dropping = fm[2].lower() in DROP_FENCES
            if not dropping:
                out.append(line)
            continue
        if fence is not None:
            if s.startswith(fence) and s.strip("`~") == "":
                fence = None
                if dropping:
                    dropping = False
                    continue
            if not dropping:
                out.append(line)
            continue
        if HEADING_RE.match(s):
            line = re.sub(r"\{\{\s*title\s*\}\}", name, line)
            line = re.sub(r"\{\{[^}]*\}\}", "", line)
            if HEADING_RE.match(line.strip()) and HEADING_RE.match(line.strip())[2]:
                out.append(line)
            continue
        if strip and ("{{" in s or EMPTY_LINK_RE.match(s) or (s in tmpl)):
            continue
        if cm := CALLOUT_RE.match(line):
            prefix = cm[1].rstrip() + " "
            if cm[3].strip():
                out.append(f"{prefix}**{curate.WIKILINK_RE.sub(link_sub, cm[3].strip())}**")
            else:
                out.append(prefix.rstrip())
            continue
        out.append(curate.WIKILINK_RE.sub(link_sub, line))

    # a bare ">" that ends a blockquote is leftover callout scaffolding
    out = [ln for i, ln in enumerate(out)
           if ln.strip() != ">" or (i + 1 < len(out) and out[i + 1].lstrip().startswith(">"))]
    if strip:
        out = _drop_empty_sections(out)
    first = next((i for i, ln in enumerate(out) if ln.strip()), None)
    if first is not None and (h := HEADING_RE.match(out[first].strip())) and len(h[1]) == 1 \
            and h[2].strip().lower() == name.strip().lower():
        out = out[first + 1:]
    text = "\n".join(out)
    if gm_notes:
        text = text.rstrip() + "\n\n## GM notes\n\n" + "\n\n".join(gm_notes)
    return _tidy(text), refs


def _drop_empty_sections(lines: list[str]) -> list[str]:
    """Remove headings whose own text and all sub-sections are empty (template scaffolding)."""
    heads = []  # (line index, level)
    fence = False
    for i, ln in enumerate(lines):
        if ln.strip().startswith(("```", "~~~")):
            fence = not fence
        elif not fence and (m := HEADING_RE.match(ln.strip())):
            heads.append((i, len(m[1])))
    if not heads:
        return lines
    keep = [True] * len(heads)
    for h in range(len(heads) - 1, -1, -1):
        i, lvl = heads[h]
        end = heads[h + 1][0] if h + 1 < len(heads) else len(lines)
        own = any(ln.strip() not in ("", ">", "---") for ln in lines[i + 1:end])
        child = False
        for k in range(h + 1, len(heads)):
            if heads[k][1] <= lvl:
                break
            child = child or keep[k]
        keep[h] = own or child
    drop = {heads[h][0] for h in range(len(heads)) if not keep[h]}
    return [ln for i, ln in enumerate(lines) if i not in drop]


def _tidy(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n") + "\n" if text.strip() else ""


# ---------------------------------------------------------------- diff + merge

def _norm(line: str) -> str:
    return " ".join(line.split())


def _word_segments(a: str, b: str) -> tuple[list, list]:
    ta = re.findall(r"\s+|\w+|[^\w\s]", a)
    tb = re.findall(r"\s+|\w+|[^\w\s]", b)
    sa, sb = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_opcodes():
        if i2 > i1:
            sa.append(["".join(ta[i1:i2]), tag != "equal"])
        if j2 > j1:
            sb.append(["".join(tb[j1:j2]), tag != "equal"])
    return sa, sb


def side_by_side(a: str, b: str) -> dict:
    al, bl = a.splitlines(), b.splitlines()
    sm = difflib.SequenceMatcher(None, [_norm(x) for x in al], [_norm(x) for x in bl], autojunk=False)
    rows, hunks, added, removed = [], 0, 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            rows += [{"t": "eq", "ln": i + 1, "rn": j + 1, "l": al[i], "r": bl[j]}
                     for i, j in zip(range(i1, i2), range(j1, j2))]
            continue
        hunks += 1
        removed += i2 - i1
        added += j2 - j1
        for k in range(max(i2 - i1, j2 - j1)):
            i, j = i1 + k, j1 + k
            row = {"t": "chg", "h": hunks}
            if i < i2:
                row.update(ln=i + 1, l=al[i])
            if j < j2:
                row.update(rn=j + 1, r=bl[j])
            if i < i2 and j < j2:
                row["ls"], row["rs"] = _word_segments(al[i], bl[j])
            rows.append(row)
    return {"rows": rows, "hunks": hunks, "added": added, "removed": removed,
            "similarity": round(sm.ratio() * 100)}


def _sections(text: str) -> list[tuple[str, list[str]]]:
    secs: list[list] = [["", []]]
    seen: Counter = Counter()
    fence = False
    for line in text.splitlines():
        if line.strip().startswith(("```", "~~~")):
            fence = not fence
        m = None if fence else HEADING_RE.match(line.strip())
        if m:
            key = re.sub(r"[^a-z0-9]+", " ", m[2].lower()).strip()
            seen[key] += 1
            secs.append([f"{key}#{seen[key]}", [line]])
        else:
            secs[-1][1].append(line)
    return [(k, v) for k, v in secs]


def _has_text(lines: list[str]) -> bool:
    return any(ln.strip() and not HEADING_RE.match(ln.strip()) for ln in lines)


def _trim(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    i, j = 0, len(lines)
    while i < j and not lines[i].strip():
        i += 1
    while j > i and not lines[j - 1].strip():
        j -= 1
    return lines[:i], lines[i:j], lines[j:]


class _Merger:
    def __init__(self, la: str, lb: str):
        self.la, self.lb, self.conflicts = la, lb, 0

    def block(self, x: list[str], y: list[str]) -> list[str]:
        nx, ny = _norm(" ".join(x)), _norm(" ".join(y))
        if not nx:
            return y
        if not ny or nx == ny or ny in nx:
            return x
        if nx in ny:
            return y
        tx, ty = re.findall(r"\w+", nx.lower()), re.findall(r"\w+", ny.lower())
        if difflib.SequenceMatcher(None, tx, ty, autojunk=False).ratio() < REWRITE_RATIO:
            return self.union(x, y)  # different material, not two takes on the same text: keep both
        pre, xm, post = _trim(x)
        _, ym, _ = _trim(y)
        self.conflicts += 1
        return [*pre, f"{CONFLICT_START} {self.la}", *xm, CONFLICT_SEP, *ym, f"{CONFLICT_END} {self.lb}", *post]

    @staticmethod
    def union(x: list[str], y: list[str]) -> list[str]:
        _, xm, post = _trim(x)
        pre, ym, _ = _trim(y)
        if not xm or not ym:
            return x + y
        listy = re.compile(r"^\s*([-*+]|\d+[.)]|\|)")
        joiner = [] if listy.match(xm[-1]) and listy.match(ym[0]) else [""]
        return [*x[:len(x) - len(post)], *joiner, *y[len(pre):], *post]

    def section(self, a: list[str], b: list[str]) -> list[str]:
        if [_norm(x) for x in a] == [_norm(x) for x in b]:
            return a
        if not _has_text(a) and (not a or not b or _norm(a[0]) == _norm(b[0]) or not a[0].startswith("#")):
            return b
        if not _has_text(b) and (not b or not a or _norm(a[0]) == _norm(b[0]) or not b[0].startswith("#")):
            return a
        out: list[str] = []
        sm = difflib.SequenceMatcher(None, [_norm(x) for x in a], [_norm(x) for x in b], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("equal", "delete"):
                out += a[i1:i2]
            elif tag == "insert":
                out += b[j1:j2]
            else:
                out += self.block(a[i1:i2], b[j1:j2])
        return out


def merge_text(a: str, b: str, la: str = "A", lb: str = "B") -> tuple[str, int]:
    """Two-way, section-aware merge. Keeps everything either side has; where both sides say
    different things in the same place, emits VS Code-style conflict markers."""
    if _norm(a) == _norm(b) or not b.strip():
        return a, 0
    if not a.strip():
        return b, 0
    A, B = _sections(a), _sections(b)
    mg = _Merger(la, lb)
    out: list[str] = []
    sm = difflib.SequenceMatcher(None, [k for k, _ in A], [k for k, _ in B], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                out += mg.section(A[i][1], B[j][1])
        elif tag == "delete":
            out += [ln for _, sec in A[i1:i2] for ln in sec]
        elif tag == "insert":
            out += [ln for _, sec in B[j1:j2] for ln in sec]
        else:
            pairs = min(i2 - i1, j2 - j1)
            for k in range(pairs):
                out += mg.section(A[i1 + k][1], B[j1 + k][1])
            out += [ln for _, sec in A[i1 + pairs:i2] for ln in sec]
            out += [ln for _, sec in B[j1 + pairs:j2] for ln in sec]
    # keep a blank line before each heading
    fixed: list[str] = []
    for ln in out:
        if (HEADING_RE.match(ln.strip()) and fixed and fixed[-1].strip()
                and not fixed[-1].startswith((CONFLICT_START, CONFLICT_SEP, CONFLICT_END))):
            fixed.append("")
        fixed.append(ln)
    return _tidy("\n".join(fixed)), mg.conflicts


# ---------------------------------------------------------------- suggestions

def _snake(k: str) -> str:
    k = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(k))
    return re.sub(r"[^a-z0-9]+", "_", k.lower()).strip("_")


def _tag(t: str) -> str:
    return "/".join(s for s in (slugify(p) for p in str(t).lstrip("#").split("/")) if s != "untitled")


def _empty(v) -> bool:
    return v is None or v == "" or v == [] or v == {}


def guess_type(members: list[dict]) -> str:
    votes: Counter = Counter()
    for w, m in enumerate(members):
        weight = len(members) - w
        raw_type = str(m["fm"].get("type") or "").lower()
        if raw_type in TYPE_HINTS:
            votes[TYPE_HINTS[raw_type]] += 3 * weight
        hay = f"{m['path']} {m['title']}".lower()
        for t, pat in PATH_HINTS:
            if re.search(pat, hay):
                votes[t] += weight
                break
    return votes.most_common(1)[0][0] if votes else "misc"


def suggest(item: dict, members: list[dict]) -> dict:
    entry = next((m for m in members if m["kind"] == "entry" and m["exists"]), None)
    raws = [m for m in members if m["kind"] == "raw" and m["exists"]]
    by_size = sorted(raws, key=lambda m: -len(m["prepared"]))
    primary = by_size[0]["key"] if by_size else None

    extras: dict = {}
    extra_conflicts: list[str] = []
    seen_vals: dict[str, dict] = {}
    for m in sorted(raws, key=lambda m: m["key"] != primary):
        for k, v in m["fm"].items():
            if str(k).lower() in UI_ONLY_KEYS or _empty(v):
                continue
            sk = _snake(k)
            if not sk or sk in STANDARD_KEYS:
                continue
            seen_vals.setdefault(sk, {})[m["label"]] = v
            extras.setdefault(sk, v)
    for k, vals in seen_vals.items():
        if len({json.dumps(v, sort_keys=True, default=str) for v in vals.values()}) > 1:
            extra_conflicts.append(f"{k}: " + "; ".join(f"{lbl} = {v}" for lbl, v in vals.items()))

    tags: list[str] = []
    aliases: list[str] = []
    for m in raws:
        t = m["fm"].get("tags") or m["fm"].get("tag") or []
        for x in ([t] if isinstance(t, str) else t):
            if (tg := _tag(x)) and tg not in tags:
                tags.append(tg)
        for k in ("aliases", "Aliases", "alias", "Alias"):
            v = m["fm"].get(k)
            for x in ([v] if isinstance(v, str) else (v or [])):
                if x and str(x) not in aliases:
                    aliases.append(str(x))

    roles = {m["key"]: ("primary" if m["key"] == primary else "merged") for m in raws}
    if entry:
        fm = entry["fm"]
        cited = {f"{s.get('source')}:{s.get('path')}": s.get("role", "merged") for s in fm.get("sources") or []}
        if cited:
            roles = {m["key"]: cited.get(m["key"], "merged") for m in raws}
            primary = next((k for k, v in roles.items() if v == "primary"), primary)
        extra = {k: v for k, v in fm.items() if k not in STANDARD_KEYS}
        for k, v in extras.items():
            extra.setdefault(k, v)
        return {
            "mode": "update", "target": entry["key"], "primary": primary, "roles": roles,
            "id": fm.get("id"), "type": fm.get("type", "misc"), "name": fm.get("name", ""),
            "slug": str(fm.get("id", "/")).split("/", 1)[1],
            "aliases": list(dict.fromkeys(list(fm.get("aliases") or []) + aliases)),
            "summary": fm.get("summary", ""), "tags": list(dict.fromkeys(list(fm.get("tags") or []) + tags)),
            "related": list(fm.get("related") or []), "status": "canonical",
            "licence": fm.get("licence") or "own-work",
            "extra_yaml": yaml.safe_dump(extra, sort_keys=False, allow_unicode=True) if extra else "",
            "extra_conflicts": extra_conflicts,
        }

    titles = [m["title"] for m in by_size] or [item["title"]]
    common = [t for t in titles if all(t.lower() in o.lower() for o in titles)]
    name = min(common, key=len) if common else titles[0]
    for t in titles:
        if t != name and t not in aliases:
            aliases.append(t)
    typ = guess_type(by_size or members)
    prim = next((m for m in raws if m["key"] == primary), None)
    return {
        "mode": "create", "target": None, "primary": primary, "roles": roles,
        "type": typ, "name": name, "slug": slugify(name), "aliases": [a for a in aliases if a != name],
        "summary": "", "tags": tags, "related": [], "status": "canonical",
        "licence": (prim or {}).get("licence") or "own-work",
        "extra_yaml": yaml.safe_dump(extras, sort_keys=False, allow_unicode=True) if extras else "",
        "extra_conflicts": extra_conflicts,
    }


def item_detail(item_id: str, strip: bool = True) -> dict:
    item = find_item(item_id)
    links = link_map()
    members = []
    for key in item["members"]:
        m = load_member(key)
        name = m["title"]
        if m["kind"] == "entry":
            m["prepared"], m["refs"] = m["body"], []
        else:
            m["prepared"], m["refs"] = prepare(m["body"], name, m["source"], strip, links)
        members.append(m)
    sug = suggest(item, members)
    return {"item": item, "members": members, "suggest": sug,
            "types": list(TYPE_DIRS), "existing_ids": sorted(v[0] for v in {*links.values()})}


# ---------------------------------------------------------------- save / dismiss

def _csv(v) -> list[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v or "").split(",") if x.strip()]


def save(payload: dict) -> dict:
    item = find_item(payload.get("id", ""))
    meta = payload.get("meta") or {}
    body = str(payload.get("body") or "")
    roles: dict = payload.get("roles") or {}
    method = str(payload.get("method") or "edited")
    note = str(payload.get("note") or "").strip()
    errors: list[str] = []

    if CONFLICT_LINE_RE.search(body):
        errors.append("The result still has conflict markers (<<<<<<< / ======= / >>>>>>>). "
                      "Resolve each conflict first.")
    if not body.strip():
        errors.append("The result body is empty.")

    typ = meta.get("type")
    name = str(meta.get("name") or "").strip()
    slug = str(meta.get("slug") or "").strip()
    if typ not in TYPE_DIRS:
        errors.append(f"Unknown type '{typ}'.")
    if not name:
        errors.append("Name is required.")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        errors.append("Slug must be lowercase letters/digits separated by single hyphens.")
    try:
        extra = yaml.safe_load(meta.get("extra_yaml") or "") or {}
        if not isinstance(extra, dict):
            raise ValueError
    except (yaml.YAMLError, ValueError):
        extra = {}
        errors.append("Extra fields must be a YAML mapping (key: value lines).")
    clash = [k for k in extra if k in STANDARD_KEYS]
    if clash:
        errors.append("Extra fields can't redefine standard fields: " + ", ".join(clash))
    if errors:
        raise ReviewError("Can't save yet.", errors)

    cid = f"{typ}/{slug}"
    target_key = next((k for k in item["members"] if k.startswith("content:")), None)
    existing_path, existing_fm = None, {}
    if target_key:
        existing_path = _content_path(target_key.removeprefix("content:"))
        if existing_path:
            existing_fm, _ = split_frontmatter(existing_path.read_text())
            if existing_fm.get("id") and existing_fm["id"] != cid:
                raise ReviewError("Can't save yet.", [
                    f"This updates existing entry '{existing_fm['id']}'. Ids are a public contract, so the "
                    "tool won't rename it. Keep the original type and slug."])
    path = CONTENT / TYPE_DIRS[typ] / f"{slug}.md"
    if existing_path is None and path.exists():
        raise ReviewError("Can't save yet.", [
            f"{path.relative_to(ROOT)} already exists and isn't part of this group. Pick another slug, "
            "or curate it together with this group."])

    # sources: keep the existing ones, then add/refresh this item's raw members
    sources = {(s.get("source"), s.get("path")): dict(s) for s in existing_fm.get("sources") or []}
    included = []
    for key in item["members"]:
        if key.startswith("content:"):
            continue
        role = roles.get(key, "merged")
        if role == "exclude":
            continue
        m = load_member(key)
        if not m["exists"] or not m["hash"]:
            continue
        sources[(m["source"], m["path"])] = {"source": m["source"], "path": m["path"], "hash": m["hash"],
                                             "role": role if role in ("primary", "merged", "superseded") else "merged"}
        included.append(m)
    src_list = list(sources.values())
    if src_list and not any(s.get("role") == "primary" for s in src_list):
        src_list[0]["role"] = "primary"
    if sum(s.get("role") == "primary" for s in src_list) > 1:
        raise ReviewError("Can't save yet.", ["Only one source can be primary."])
    if not src_list:
        raise ReviewError("Can't save yet.", ["Include at least one source file (all are set to 'exclude')."])

    images = list(existing_fm.get("images") or [])
    for href in ASSET_RE.findall(body):
        p = unquote(href.lstrip("/"))
        if p not in images:
            images.append(p)

    raw_aliases = meta.get("aliases")
    raw_aliases = raw_aliases if isinstance(raw_aliases, list) else str(raw_aliases or "").splitlines()
    aliases = [a for a in dict.fromkeys(str(x).strip() for x in raw_aliases) if a and a != name]
    fm = {"id": cid, "type": typ, "name": name}
    if aliases:
        fm["aliases"] = aliases
    if str(meta.get("summary") or "").strip():
        fm["summary"] = " ".join(str(meta["summary"]).split())
    if existing_fm.get("setting"):
        fm["setting"] = existing_fm["setting"]
    if tags := list(dict.fromkeys(_csv(meta.get("tags")))):
        fm["tags"] = tags
    if related := list(dict.fromkeys(_csv(meta.get("related")))):
        fm["related"] = related
    fm["status"] = meta.get("status") or "canonical"
    fm["sources"] = src_list
    fm["licence"] = str(meta.get("licence") or "own-work")
    if images:
        fm["images"] = images
    fm["updated"] = today()
    fm.update(extra)

    # validate the same way `dndres validate` would
    schema = json.loads((ROOT / "schemas" / "entry.schema.json").read_text())
    try:
        jsonschema.validate(_jsonable(fm), schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema: {e.message} at {'/'.join(map(str, e.path)) or '(root)'}")
    known = {f.get("id") for _, f, _ in iter_content()} | {cid}
    errors += [f"Related id '{r}' does not exist." for r in fm.get("related", []) if r not in known]
    stripped = curate.CODEBLOCK_RE.sub("", body)
    errors += [f"Unresolved wikilink [[{w[0]}]]: make it plain text or a /content/... link."
               for w in curate.WIKILINK_RE.findall(stripped)]
    for _, href in curate.MDLINK_RE.findall(stripped):
        if href.startswith("/content/") and not (ROOT / unquote(href.lstrip("/"))).exists():
            errors.append(f"Broken link {href}")
        elif href.startswith("/assets/") and not (ROOT / unquote(href.lstrip("/"))).exists():
            errors.append(f"Missing asset {href}")
    if errors:
        raise ReviewError("Can't save yet.", errors)

    with _write_lock:
        if existing_path and existing_path != path:
            raise ReviewError("Can't save yet.", ["Existing entry lives at a different path; fix it with `dndres validate`."])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(join_frontmatter(fm, body.rstrip() + "\n"))

        labels = {m["key"]: f"{m['label']} ({m['path']})" for m in included}
        prim = next((labels.get(f"{s['source']}:{s['path']}") for s in src_list if s.get("role") == "primary"), None)
        excluded = [k for k in item["members"] if roles.get(k) == "exclude"]
        how = {"merge": "merged", "merge+edit": "merged, then edited", "use": "took one version",
               "use+edit": "took one version, then edited", "edited": "written by hand"}.get(method, method)
        decision = f"Saved as `{cid}` ({how}"
        decision += f"; primary {prim}" if prim else ""
        decision += f"; excluded {', '.join(excluded)}" if excluded else ""
        decision += ")"
        if item["kind"] == "duplicate":
            keys = sorted(set(item["members"]) | {f"content:{cid}"})
            curate.log_decision(curate.dupes_scope(keys), f'Duplicate group "{item["title"]}": how to combine?',
                                decision, note)
            remove_duplicate(item["id"])
        else:
            curate.log_decision(f"`{cid}`", item["title"], decision, note)
            remove_conflict(item["id"])
        curate.build_index()
    return {"ok": True, "id": cid, "path": str(path.relative_to(ROOT)),
            "message": f"Saved {cid} → {path.relative_to(ROOT)}"}


DISMISS_REASONS = {
    "separate": "Not duplicates: keep as separate things",
    "stubs": "Stubs: nothing worth keeping, leave uncurated",
    "identical-drop": "Not worth an entry",
}


def dismiss(payload: dict) -> dict:
    item = find_item(payload.get("id", ""))
    if item["kind"] != "duplicate":
        raise ReviewError("Conflicts can't be dismissed: save a resolution instead.")
    reason = DISMISS_REASONS.get(payload.get("reason"), str(payload.get("reason") or "Dismissed"))
    with _write_lock:
        curate.log_decision(curate.dupes_scope(sorted(item["members"])),
                            f'Duplicate group "{item["title"]}": same thing?', reason,
                            str(payload.get("note") or "").strip())
        remove_duplicate(item["id"])
    return {"ok": True, "message": f'Dismissed "{item["title"]}": {reason}'}


def list_items() -> dict:
    d = parse_duplicates()
    return {"duplicates": d["items"], "conflicts": parse_conflicts(), "generated": d["generated"],
            "stubs": d["stubs"], "dismiss_reasons": DISMISS_REASONS}


def rescan() -> dict:
    with _write_lock:
        curate.dupes()
    _template_cache.clear()
    return {"ok": True, "message": "Re-ran `dndres dupes`."}


# ---------------------------------------------------------------- HTTP server

STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
          "/app.css": ("app.css", "text/css; charset=utf-8")}


def make_handler(token: str, allowed_hosts: set[str]):
    class Handler(BaseHTTPRequestHandler):
        server_version = "dndres-review/1"

        def log_message(self, fmt, *args):  # quiet: only log writes
            if self.command == "POST":
                print(f"  {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, data) -> None:
            self._send(status, json.dumps(data, ensure_ascii=False, default=str).encode(), "application/json")

        def _host_ok(self) -> bool:
            if self.headers.get("Host", "") not in allowed_hosts:
                self._json(403, {"error": "Bad Host header"})
                return False
            return True

        def do_GET(self):
            if not self._host_ok():
                return
            url = urlparse(self.path)
            try:
                if url.path in STATIC:
                    fname, ctype = STATIC[url.path]
                    data = (UI_DIR / fname).read_text()
                    if fname == "index.html":
                        data = data.replace("__DNDRES_TOKEN__", token)
                    return self._send(200, data.encode(), ctype)
                q = {k: v[0] for k, v in parse_qs(url.query).items()}
                if url.path == "/api/items":
                    return self._json(200, list_items())
                if url.path == "/api/item":
                    return self._json(200, item_detail(q.get("id", ""), q.get("strip", "1") != "0"))
                self._json(404, {"error": "Not found"})
            except ReviewError as e:
                self._json(e.status, {"error": str(e), "details": e.details})
            except Exception as e:  # noqa: BLE001
                self._json(500, {"error": f"{type(e).__name__}: {e}"})

        def do_POST(self):
            if not self._host_ok():
                return
            if self.headers.get("X-Dndres-Token") != token:
                return self._json(403, {"error": "Missing or bad token. Reload the page."})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(n) or b"{}")
                path = urlparse(self.path).path
                if path == "/api/diff":
                    return self._json(200, side_by_side(str(payload.get("a", "")), str(payload.get("b", ""))))
                if path == "/api/merge":
                    text, n_conf = merge_text(str(payload.get("a", "")), str(payload.get("b", "")),
                                              str(payload.get("a_label") or "A"), str(payload.get("b_label") or "B"))
                    return self._json(200, {"text": text, "conflicts": n_conf})
                if path == "/api/save":
                    return self._json(200, save(payload))
                if path == "/api/dismiss":
                    return self._json(200, dismiss(payload))
                if path == "/api/rescan":
                    return self._json(200, rescan())
                self._json(404, {"error": "Not found"})
            except ReviewError as e:
                self._json(e.status, {"error": str(e), "details": e.details})
            except Exception as e:  # noqa: BLE001
                self._json(500, {"error": f"{type(e).__name__}: {e}"})

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    token = secrets.token_urlsafe(24)
    httpd = None
    for p in range(port, port + 20):
        allowed = {f"{h}:{p}" for h in ("127.0.0.1", "localhost", host)}
        try:
            httpd = ThreadingHTTPServer((host, p), make_handler(token, allowed))
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        raise SystemExit(f"No free port in {port}-{port + 19}. Try --port.")
    url = f"http://{'localhost' if host in ('127.0.0.1', '0.0.0.0') else host}:{port}/"
    d = parse_duplicates()
    print(f"dndres review: {len(d['items'])} duplicate groups, {len(parse_conflicts())} open conflicts")
    print(f"Serving on {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        httpd.server_close()
