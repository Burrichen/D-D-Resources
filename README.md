# D&D Resources

A curated, deduplicated library of D&D material (homebrew world, rules, tables) built from Obsidian vaults, Miraheze wikis, web pages and Google Docs. It is meant to be read by other programs.

## For consuming programs

Read from **`index/`** and **`content/`** only. `raw/` is an unreviewed staging area.

### `index/manifest.json`

```jsonc
{
  "generated": "2026-11-04T…",
  "count": 123,
  "by_type": {"character": 40, "location": 31, …},
  "aliases": {"god of the dead": "deity/kelemvor", …},   // lower-cased name/alias → id
  "entries": [
    {"id": "deity/kelemvor", "type": "deity", "name": "Kelemvor", "aliases": […],
     "summary": "…", "tags": […], "related": ["location/…"], "status": "canonical",
     "updated": "2026-11-04", "images": […], "path": "content/deities/kelemvor.md",
     "fields": {"alignment": "LN", "domains": […]}}
  ]
}
```

### `index/entries.jsonl`

Contains the same records as the manifest, plus each entry's markdown `body`, one entry per line.

### Content files

Each file in `content/<type>/<slug>.md` has YAML frontmatter, validated against [`schemas/entry.schema.json`](schemas/entry.schema.json), followed by a GitHub-flavoured markdown body. How to handle the body:

- Links between entries are root-relative, like `/content/<dir>/<slug>.md`.
- Image paths are root-relative, like `/assets/...`.
- Images are stored in Git LFS, so run `git lfs pull` after cloning.
- Statblocks appear as fenced blocks tagged `statblock` and containing YAML.

### Stability

- An `id` never changes meaning.
- A superseded entry is set to `status: deprecated` and gets a `superseded_by` field.
- Filter on `status` (`canonical`, `draft`, `needs-review`, `deprecated`) to decide what you trust.
- Filter on `licence` before publishing anything. `proprietary - personal reference only` must not be redistributed.

## Maintaining

```sh
uv sync                       # first time
uv run dndres ingest --all    # refresh all sources into raw/
uv run dndres status          # what needs curating
uv run dndres dupes           # duplicate candidates → review/duplicates.md
uv run dndres validate && uv run dndres index
```

Sources are registered in [`sources.yaml`](sources.yaml). Curation is done with Claude Code using the skills in `.claude/skills/`. See [CLAUDE.md](CLAUDE.md).

## Layout

| Path | What's there |
|---|---|
| `sources.yaml` | Registry of every source. |
| `raw/<source-id>/` | Ingested markdown with provenance frontmatter. Machine-written. |
| `assets/<source-id>/` | Images and PDFs referenced by notes (Git LFS). |
| `content/<type>/` | Canonical entries. |
| `index/` | Generated JSON for programs. |
| `review/` | Duplicate reports, the conflict queue, and the decision log. |
| `schemas/` | JSON Schema for entry frontmatter. |
| `src/dndres/` | Ingest and curation tooling. |
