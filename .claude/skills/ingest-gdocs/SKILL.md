---
name: ingest-gdocs
description: Pull link-shared Google Docs into this repo's raw/ store. Use when the user pastes a docs.google.com/document link or asks to import session notes, lore docs, or anything else from Google Docs.
---

# Ingest Google Docs

This works through the public export endpoint, so docs **must be shared as "Anyone with the link: Viewer"**. No Google credentials are used.

## Steps

1. **Pick or create a source.** Group docs by purpose, e.g. `gdoc-session-notes` or `gdoc-lore`. In `sources.yaml` use `type: gdoc`, `urls: [...]`, `licence: own-work` (if it is the user's), and `priority`.
2. **Ingest.** Either:
   - all listed URLs: `uv run dndres ingest <id>`
   - one new doc: `uv run dndres ingest <id> --url <docs.google.com URL>`. After it works, also add the URL to that source's `urls:` so future refreshes include it.
3. **If it fails with "not link-shared"**, ask the user to change the sharing setting. Don't try other auth routes.
4. **How docs are stored:**
   - Markdown export is tried first. Inline images are extracted to `assets/<id>/<doc-id>/`.
   - If Markdown export fails, it falls back to .docx and pandoc.
   - Files are named `<title-slug>--<docid8>.md`. If a doc is renamed, the next pull writes a new file, and the old one stays (gdoc sources are not pruned). Delete the old raw file and its `_manifest.json` entry only after `curate` has repointed any content `sources:` at the new path.
5. Run `uv run dndres dupes`. Google Docs often duplicate vault notes (copy-pasted session notes), so check for this explicitly.

## Rules

- Never edit `raw/` by hand.
- Docs often mix several topics (one doc of session notes covers many NPCs). That is expected. `curate` splits them into separate entries, each citing the same raw source.
