# D&D Resources

This repo is a single, deduplicated library of D&D material (mostly the user's homebrew world), built from several sources, for other programs to consume.

## Pipeline

```
sources.yaml ──ingest──▶ raw/<source-id>/   (verbatim-ish markdown + provenance, machine-written)
                         assets/<source-id>/ (images etc., Git LFS)
raw/ ──curate (Claude + user)──▶ content/<type-dir>/<slug>.md   (canonical, one entry per thing)
content/ ──dndres index──▶ index/manifest.json, index/entries.jsonl   (what programs read)
```

## Commands

All commands run as `uv run dndres <cmd>`.

| Command | What it does |
|---|---|
| `sources` | List the registered sources. |
| `ingest <id>` / `ingest --all` / `ingest <id> --url URL` / `--dry-run` | Pull sources into `raw/`. Incremental, using content hashes. |
| `status [-v]` | Count uncurated, curated and stale raw files, and list orphaned source references. |
| `dupes` | Regenerate `review/duplicates.md` and `review/duplicates.json`, the duplicate candidates and stub list. |
| `validate` | Check `content/` against the schema, file locations, links, and source references. Must pass before committing. |
| `index` | Rebuild `index/`. Run it after any change to `content/`. |

## Skills (`.claude/skills/`)

- `ingest-obsidian`: Obsidian vaults.
- `ingest-wiki-web`: Miraheze, MediaWiki and plain web pages.
- `ingest-gdocs`: link-shared Google Docs.
- `curate`: dedupe, merge, organise, and resolve conflicts. **Read it before touching `content/`.**

## Ground rules

- `raw/` is machine-written. Never hand-edit it; re-ingest instead. Never write to the source vaults or docs.
- **Conflicts between sources are always put to the user**, one question per conflict, batched. Decisions are logged in `review/decisions.md` and never re-asked. Open conflicts live in `review/conflicts.md`.
- Canonical ids (`<type>/<slug>`) are a public contract with consumer programs:
  - Don't rename an id. If you must, add the old name to `aliases`.
  - Don't delete an entry. Deprecate it instead.
- Every content entry lists its `sources` with the raw `_content_hash`. That is how `status` detects stale entries after a re-ingest.
- Record `licence` for anything that isn't the user's own work. Third-party, non-SRD material is marked `proprietary - personal reference only`.
- Generated files are `review/duplicates.*` and `index/*`. Regenerate them; don't edit them.

## Known sources (as of 2026-11-04)

| Vault | Notes | State |
|---|---|---|
| v2 | 190 | Largest. Characters, locations, gods, campaigns, homebrew mechanics. |
| v3 | 38 | Lore, cosmology (World Tree), Ordon. |
| v4 | 63 | Halingo, Ordon. Many empty scaffold notes. |
| V5 | 4 | Scaffold only. |

All four look like successive versions of the same world, so expect overlapping places and gods (Ordon, Halingo, Heresy, Kelemvor, Timeline).
