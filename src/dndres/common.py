"""Shared helpers: repo paths, sources registry, frontmatter, raw-file writing."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "raw"
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
INDEX = ROOT / "index"
REVIEW = ROOT / "review"
SOURCES_FILE = ROOT / "sources.yaml"

USER_AGENT = "DnD-Resources-ingest/0.1 (personal archive tool)"

TYPE_DIRS = {
    "character": "characters", "location": "locations", "faction": "factions",
    "deity": "deities", "species": "species", "creature": "creatures", "item": "items",
    "spell": "spells", "mechanic": "mechanics", "table": "tables", "lore": "lore",
    "event": "events", "campaign": "campaigns", "story": "stories", "misc": "misc",
}

_FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)


# ---------- sources.yaml ----------

def load_sources() -> list[dict]:
    data = yaml.safe_load(SOURCES_FILE.read_text()) or {}
    return data.get("sources", [])


def get_source(source_id: str) -> dict:
    for s in load_sources():
        if s["id"] == source_id:
            return s
    raise SystemExit(f"Unknown source id '{source_id}'. Add it to sources.yaml first.")


def set_source_field(source_id: str, key: str, value: str) -> None:
    """Update a scalar field for one source in sources.yaml without losing comments."""
    lines = SOURCES_FILE.read_text().splitlines(keepends=True)
    in_block = False
    for i, line in enumerate(lines):
        m = re.match(r"\s*- id:\s*(\S+)", line)
        if m:
            in_block = m.group(1) == source_id
            continue
        if in_block and re.match(rf"\s+{re.escape(key)}:", line):
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = f"{indent}{key}: {json.dumps(value)}\n"
            SOURCES_FILE.write_text("".join(lines))
            return
    raise SystemExit(f"Could not find '{key}' for source '{source_id}' in sources.yaml")


# ---------- text utils ----------

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    return dt.date.today().isoformat()


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "untitled"


def safe_relpath(text: str) -> str:
    """Make a filesystem-safe relative path segment (keeps readability)."""
    text = re.sub(r'[<>:"\\|?*\x00-\x1f]', "", text).strip().strip(".")
    return text or "untitled"


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
        if not isinstance(fm, dict):
            fm = {"_unparsed_frontmatter": m.group(1)}
    except yaml.YAMLError:
        fm = {"_unparsed_frontmatter": m.group(1)}
    return fm, text[m.end():]


def join_frontmatter(fm: dict, body: str) -> str:
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=1000)
    return f"---\n{dumped}---\n\n{body.lstrip()}"


def _jsonable(v: Any) -> Any:
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    return v


# ---------- raw store ----------

class RawWriter:
    """Writes provenance-stamped markdown into raw/<source>/ and tracks a manifest.

    The manifest (raw/<source>/_manifest.json) maps raw path -> content hash, so
    re-ingesting reports added / changed / unchanged / removed files.
    """

    def __init__(self, source: dict):
        self.source = source
        self.dir = RAW / source["id"]
        self.dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.dir / "_manifest.json"
        self.old = json.loads(self.manifest_path.read_text()) if self.manifest_path.exists() else {}
        self.new: dict[str, str] = {}
        self.stats = {"added": 0, "changed": 0, "unchanged": 0}

    def write(self, rel_path: str, body: str, *, content_hash: str, meta: dict | None = None,
              original_fm: dict | None = None) -> Path:
        rel_path = rel_path if rel_path.endswith(".md") else rel_path + ".md"
        self.new[rel_path] = content_hash
        prev = self.old.get(rel_path)
        dest = self.dir / rel_path
        if prev == content_hash and dest.exists():
            self.stats["unchanged"] += 1
            return dest
        self.stats["changed" if prev else "added"] += 1
        fm = {
            "_source": self.source["id"],
            "_source_path": rel_path,
            **{f"_{k}": v for k, v in (meta or {}).items() if v is not None},
            "_licence": self.source.get("licence"),
            "_fetched": now_iso(),
            "_content_hash": content_hash,
        }
        fm.update(_jsonable(original_fm or {}))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(join_frontmatter(fm, body))
        return dest

    def finish(self, *, prune: bool = True) -> dict:
        removed = sorted(set(self.old) - set(self.new))
        if prune:
            for rel in removed:
                p = self.dir / rel
                if p.exists():
                    p.unlink()
        self.manifest_path.write_text(json.dumps(dict(sorted(self.new.items())), indent=1))
        set_source_field(self.source["id"], "last_pulled", now_iso())
        return {**self.stats, "removed": removed}


def print_stats(source_id: str, stats: dict) -> None:
    removed = stats.get("removed", [])
    print(f"[{source_id}] added={stats['added']} changed={stats['changed']} "
          f"unchanged={stats['unchanged']} removed={len(removed)}")
    for r in removed[:20]:
        print(f"  removed: {r}")


def iter_raw(source_id: str | None = None):
    """Yield (source_id, rel_path, frontmatter, body) for every raw markdown file."""
    dirs = [RAW / source_id] if source_id else sorted(p for p in RAW.iterdir() if p.is_dir())
    for d in dirs:
        for p in sorted(d.rglob("*.md")):
            fm, body = split_frontmatter(p.read_text())
            yield d.name, str(p.relative_to(d)), fm, body


def iter_content():
    """Yield (path, frontmatter, body) for every canonical entry."""
    for p in sorted(CONTENT.rglob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        yield p, fm, body
