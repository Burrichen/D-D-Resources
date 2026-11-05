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

## Reviewing duplicates and conflicts (`dndres review`)

`dndres review` opens a local web page for working through `review/duplicates.md` and `review/conflicts.md`. You can compare versions side by side, pick one, merge them, edit the result, and save it as a canonical entry.

```sh
uv run dndres dupes     # (re)generate review/duplicates.md first if it's stale
uv run dndres review    # starts http://localhost:8765/ and opens your browser
```

| Option | Default | What it does |
|---|---|---|
| `--port N` | `8765` | Port to serve on. If it's busy, the next free port is used. |
| `--host H` | `127.0.0.1` | Interface to bind. Leave this alone unless you know you want LAN access. |
| `--no-browser` | off | Don't open a browser tab automatically. |

Press `Ctrl+C` in the terminal to stop the server. Nothing needs installing: the server uses only the Python standard library and the page loads nothing from the internet.

### The list (left)

The list shows every open conflict, then every duplicate group, read fresh from the two `.md` files. They are re-read whenever you click **Refresh**, switch back to the tab, or save. **Re-scan** re-runs `dndres dupes` from inside the page. Each group shows its flag (`IDENTICAL`, `review`, `all stubs`, `has canonical`), how many files it has, which vaults they come from, and why they were grouped. Use the filter box to search by name or path.

### The resolver (right)

Click an item to open it. The layout follows VS Code's merge editor.

1. **Compare.** The top half is a side-by-side diff of **A** and **B**. Red lines are only in A and green lines are only in B. The brighter highlight marks the words that changed. Groups with more than two files have a dropdown on each side to choose which pair to compare.
   - **↑ / ↓** jump between changes.
   - **Hide unchanged** folds identical stretches. Click a fold to expand it.
   - **Prepared** shows the text as it would be saved: `[[wikilinks]]` become links, or plain text if the target isn't curated yet. Dataview and ccard blocks are removed, `%% comments %%` move to a `## GM notes` section, and callout markers are simplified. **Original** shows exactly what's in `raw/`.
   - **Strip template scaffolding** (Prepared view only) drops lines copied from your Obsidian templates (read from each vault's template folder), along with any headings that are left with nothing under them.
2. **Build the result.** The editor in the bottom half is what gets saved.
   - **Use A** or **Use B** takes one version as-is.
   - **Merge A + B** combines both versions, section by section (`## headings`):
     - Matching sections are merged line by line, and sections only one side has are kept in place.
     - Where the two sides have different material, both are kept.
     - Where they word the same passage differently, the result gets a conflict block:
       ```
       <<<<<<< v2 · Wiki/Gods/Major/Kelemvor, God of the Dead.md
       …A's wording…
       =======
       …B's wording…
       >>>>>>> v3 · Lore/Gods and Scions/Scions/Kelemvor.md
       ```
       The conflict bar above the editor has **Accept A**, **Accept B** and **Accept both** for each block, plus **Prev** and **Next**. You can also just edit the text.
   - **Merge into result** (on each side) merges that version into whatever is in the result already. Use it to fold in a third file.
   - The editor is plain text, so you can type anywhere. `⌘Z` / `Ctrl+Z` undoes edits and accepts alike.
3. **Check the entry details** in the right-hand panel: type, name, slug (the id is `type/slug`), aliases (one per line), summary, tags, related ids, status and licence. **Extra fields** takes type-specific fields as YAML, pre-filled from the notes' frontmatter. If the files' frontmatter disagrees, a yellow box lists the differences. A blue box lists links that turned into plain text because their target isn't curated yet.
4. **Choose each file's role** in the header: `primary`, `merged`, `superseded`, or `exclude`. Excluded files are left uncurated and aren't cited.
5. **Save entry** (`⌘S` / `Ctrl+S`). The tool then:
   - checks the entry the same way `dndres validate` does: schema, related ids, no leftover wikilinks, links and assets that exist, and no remaining conflict markers;
   - writes `content/<type-dir>/<slug>.md`, citing each included file in `sources` with its current `_content_hash`, and listing any `/assets/…` images under `images`;
   - **removes the item from `review/duplicates.md` (and `.json`) or `review/conflicts.md`**;
   - appends the decision to `review/decisions.md`, with the optional note;
   - rebuilds `index/`;
   - moves on to the next item.

   For a conflict, or a group that already includes a canonical entry, Save updates that entry instead. Its id can't change, existing sources are kept, and the entry's text is loaded into the result to start from.

**Dismiss…** is for groups that aren't really the same thing, like Session 16 and Session 17, or for stubs not worth keeping. It removes the group and logs why, and writes no content. **Skip** goes to the next item and changes nothing.

### Decisions stay decided

`dndres dupes` regenerates `duplicates.md`, but it no longer raises a group that is already settled. A group counts as settled when one canonical entry cites all its files, or when every pair of files in it is covered by a `dupes:` row in `review/decisions.md`, which is what Save and Dismiss write. If a new file turns up that matches a settled group, only the new pairings are raised.

### Conflict format

`dndres review` reads `review/conflicts.md` entries in this shape. Claude writes them through the curate skill:

```markdown
## deity/kelemvor: Kelemvor's alignment
- Entry: `deity/kelemvor`
- `obsidian-dnd-v2:Wiki/Gods/Major/Kelemvor, God of the Dead.md`: True Neutral
- `obsidian-dnd-v3:Lore/Gods and Scions/Scions/Kelemvor.md`: Lawful Neutral
Optional free-text context.
```

## Layout

Material flows **raw → cleaned (`content/`) → Canon**. The diagram and the rules for each stage are in [CLAUDE.md › The flow](CLAUDE.md#the-flow-raw--cleaned--canon).

| Path | What's there |
|---|---|
| `sources.yaml` | Registry of every source. |
| `raw/<source-id>/` | Ingested markdown with provenance frontmatter. Machine-written. |
| `assets/<source-id>/` | Images and PDFs referenced by notes (Git LFS). |
| `content/<type>/` | Cleaned entries: one per thing, deduped across sources. |
| `Canon/<type>/` | Kurovia world lore, promoted from `content/` once approved. The final version. See [Canon/README.md](Canon/README.md). |
| `To place/` | Purpose not yet defined. |
| `index/` | Generated JSON for programs. |
| `review/` | Duplicate reports, the conflict queue, and the decision log. |
| `schemas/` | JSON Schema for entry frontmatter. |
| `src/dndres/` | Ingest and curation tooling. |
