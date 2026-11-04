"""Ingest an Obsidian vault into raw/<source>/.

Raw output stays close to the vault: wikilinks, callouts, note embeds and plugin code
blocks (dataview, chronos, statblock, ccard...) are preserved verbatim so nothing is
lost. Only *attachment* embeds are rewritten, to point at the copied file under
assets/<source>/. Interpreting plugin blocks is the curate step's job.
"""
from __future__ import annotations

import fnmatch
import os
import re
import shutil
from pathlib import Path

from .common import ASSETS, RawWriter, print_stats, sha256, split_frontmatter

SKIP_DIRS = {".obsidian", ".trash", ".git", ".stfolder"}
ATTACH_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif",
              ".pdf", ".mp3", ".wav", ".ogg", ".mp4", ".webm"}

EMBED_RE = re.compile(r"!\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\((?!https?://)([^)\s]+)\)")


def _skipped(rel: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel, p.rstrip("/*")) for p in patterns)


def ingest(source: dict, *, dry_run: bool = False) -> None:
    vault = Path(os.path.expanduser(source["path"]))
    if not (vault / ".obsidian").exists():
        raise SystemExit(f"{vault} does not look like an Obsidian vault (no .obsidian/).")
    skip = source.get("skip", []) or []

    md_files: list[Path] = []
    attachments: dict[str, list[Path]] = {}
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = str(p.relative_to(vault))
            if p.suffix.lower() == ".md":
                if not _skipped(rel, skip):
                    md_files.append(p)
            elif p.suffix.lower() in ATTACH_EXT:
                attachments.setdefault(fn.lower(), []).append(p)
                attachments.setdefault(rel.lower(), []).append(p)

    asset_root = ASSETS / source["id"]
    copied: set[Path] = set()
    missing: set[str] = set()

    def resolve(target: str) -> str | None:
        target = target.strip()
        cands = attachments.get(target.lower()) or attachments.get(Path(target).name.lower())
        if not cands:
            if Path(target).suffix.lower() in ATTACH_EXT:
                missing.add(target)
            return None
        src = cands[0]
        rel = src.relative_to(vault)
        if not dry_run and src not in copied:
            dest = asset_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.stat().st_size != src.stat().st_size:
                shutil.copy2(src, dest)
            copied.add(src)
        return f"/assets/{source['id']}/{rel.as_posix()}"

    def embed_sub(m: re.Match) -> str:
        target, opts = m.group(1), m.group(2)
        url = resolve(target)
        if url is None:
            return m.group(0)  # note embed or missing attachment: keep verbatim
        alt = Path(target).stem
        size = f" <!-- obsidian size: {opts.strip()} -->" if opts and opts.strip() else ""
        return f"![{alt}]({url.replace(' ', '%20')}){size}"

    def mdimg_sub(m: re.Match) -> str:
        url = resolve(m.group(2).replace("%20", " "))
        return f"![{m.group(1)}]({url.replace(' ', '%20')})" if url else m.group(0)

    writer = None if dry_run else RawWriter(source)
    for p in sorted(md_files):
        rel = p.relative_to(vault).as_posix()
        data = p.read_bytes()
        text = data.decode("utf-8", errors="replace")
        fm, body = split_frontmatter(text)
        body = EMBED_RE.sub(embed_sub, body)
        body = MD_IMG_RE.sub(mdimg_sub, body)
        if dry_run:
            continue
        writer.write(rel, body, content_hash=sha256(data), original_fm=fm,
                     meta={"title": p.stem})

    if dry_run:
        print(f"[{source['id']}] dry run: {len(md_files)} notes would be ingested.")
    else:
        print_stats(source["id"], writer.finish())
        print(f"  attachments copied/linked: {len(copied)}")
    if missing:
        print(f"  attachments referenced but not found in vault ({len(missing)}): "
              + ", ".join(sorted(missing)[:10]) + (" ..." if len(missing) > 10 else ""))
