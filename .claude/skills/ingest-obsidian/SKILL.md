---
name: ingest-obsidian
description: Pull or refresh an Obsidian vault into this repo's raw/ store. Use when the user mentions an Obsidian vault, a folder of markdown notes, "sync my vault", "re-import v4", or adds a new vault path. Handles registration in sources.yaml, attachments, and the post-ingest duplicate scan.
---

# Ingest an Obsidian vault

Raw ingest is mechanical and lossless. It does **not** decide what is canonical; that is the `curate` skill's job.

## Steps

1. **Register the vault** (skip if already in `sources.yaml`):
   - `id`: `obsidian-<slug>` (e.g. `obsidian-dnd-v6`). Ids are permanent, because they are cited in content frontmatter.
   - `path`: the vault root (the folder containing `.obsidian/`). `~` is fine.
   - `priority`: higher = newer. Existing vaults: v2=2, v3=3, v4=4, V5=5.
   - `skip`: glob patterns (relative to the vault) for templates, scripts and scaffolding. Look at the top-level folders first. Anything named `Templates`, `Scripts` or `z. Templates` should normally be skipped.
   - `licence: own-work` for the user's own vaults.
2. **Dry run:** `uv run dndres ingest <id> --dry-run`. Sanity-check the note count against `find <vault> -name '*.md' | wc -l`.
3. **Ingest:** `uv run dndres ingest <id>`. Re-running is safe: unchanged notes are skipped by hash, and notes deleted from the vault are removed from `raw/` (they are listed in the output).
4. **Report** the added/changed/removed counts and any "attachments referenced but not found". Those are broken embeds in the vault itself, so tell the user rather than trying to fix them.
5. **Rescan:** run `uv run dndres dupes` and `uv run dndres status`. Summarise any new duplicate groups and any STALE entries (canonical content whose source changed). Offer to run the `curate` skill on them.

## What the converter does and doesn't do

- Original note frontmatter is kept, merged under the provenance keys (`_source`, `_source_path`, `_content_hash`, ...).
- `![[image.png|500]]` becomes `![image](/assets/<id>/<path>)`. The image is copied to `assets/<id>/` (Git LFS).
- These are left **verbatim** for curation to interpret: `[[wikilinks]]`, `![[note embeds]]`, callouts (`> [!infobox]`, `> [!column]`), `%% comments %%`, and plugin code blocks (`dataview`, `dataviewjs`, `chronos`, `statblock`, `ccard`).

## Rules

- Never edit files in `raw/` by hand. Fix things in the source and re-ingest, or fix them during curation.
- Never write to the user's vault.
- If a vault is in iCloud or a sync folder and files are missing, they may be evicted (cloud-only), so tell the user.
