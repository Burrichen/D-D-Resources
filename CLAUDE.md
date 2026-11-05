# D&D Resources

This repo is a single, deduplicated library of D&D material (mostly the user's homebrew world), built from several sources, for other programs to consume.

## The flow: Raw → Cleaned → Canon

Everything moves left to right, one stage at a time. Nothing skips a stage, and nothing flows backwards.

```
  SOURCES              1. RAW                  2. CLEANED               3. CANON
  (sources.yaml)       raw/<source-id>/        content/<type-dir>/      Canon/<type-dir>/
                       assets/<source-id>/

  Obsidian vaults ─┐
  Miraheze / web  ─┼──ingest──▶  RAW  ──curate──▶  CLEANED  ──promote──▶  CANON
  Google Docs     ─┘                                  │                     │
                                                      └─────┬───────────────┘
                                                            ▼
                                                     dndres index ──▶ index/  (JSON for programs)

  RAW       As imported, machine-written. Never hand-edited.
            Goal: nothing left waiting to be curated (`dndres status` shows 0 uncurated).
  CLEANED   One entry per thing, merged across sources, deduped, schema-valid.
            Holds every kind of material. Rules, tables, spells, session logs and
            generic D&D material (Kelemvor, Tyr...) stay here for good.
  CANON     The lore of the world of Kurovia, and nothing else. User-approved, no errors,
            no duplicates, simply laid out. Other projects reference this folder directly.
```

| Stage | Folder | Written by | Rules |
|---|---|---|---|
| 1. Raw | `raw/<source-id>/`, `assets/<source-id>/` | `dndres ingest` only | Never hand-edit; re-ingest instead. "Empty" means nothing uncurated. **Don't delete raw files**: `sources` hashes, `status` and `validate` depend on them. |
| 2. Cleaned | `content/<type-dir>/<slug>.md` | Claude (`curate` skill) and the user (`dndres review`) | One entry per real thing. Conflicts go to the user. See the `curate` skill. |
| 3. Canon | `Canon/<type-dir>/<slug>.md` | Claude, **only with the user's approval** | See "Canon" below and `Canon/README.md`. |

### Canon

- **Kurovia world lore only.** Characters, places, factions, deities, species, creatures, items, events, lore and stories that belong to Kurovia. Mechanics, tables, spells, campaign/session logs, `misc`, and anything borrowed from published D&D stay in `content/`.
- **Promotion is a move, never a copy.** The entry keeps the same id and slug, goes to `Canon/<type-dir>/<slug>.md`, and is removed from `content/`. Never leave a stub or second copy behind; that would be a duplicate. Programs that use ids are unaffected.
- **Promote only what's ready, and only with approval.** Ready means `status: canonical`, no open item in `review/conflicts.md` or `review/duplicates.md`, `validate` passes, and the user has said yes to that batch. Propose batches; don't promote on your own initiative.
- **Canon outranks everything.** If raw or cleaned material contradicts Canon, Canon wins. Still tell the user about the contradiction; never quietly drop it, and never edit Canon to match a source without asking.
- **Editing Canon needs the user's say-so** for each change, including fixing typos or links. If the user drops a hand-written file into `Canon/`, it's canon as written: offer to put it into entry format, but don't change what it says.
- **Not wired up yet.** The `dndres` commands only read `content/`. Before the first promotion, `validate`, `index`, `dupes`, `status` and `review` must be taught to read `Canon/` too. Until then, don't move anything into `Canon/`.

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
| `review [--port N] [--no-browser]` | Local web UI for the user to resolve `review/duplicates.md` and `review/conflicts.md`: diff, pick, merge, edit, save. Saving writes the content entry, removes the item from the `.md`, logs to `decisions.md` and rebuilds `index/`. See README › Reviewing duplicates and conflicts. |

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

## User folders (repo root)

- `Canon/`: stage 3 of the flow above.
- `To place/`: purpose not yet defined. Don't move things in or out of it without asking.

## Known sources (as of 2026-11-04)

| Vault | Notes | State |
|---|---|---|
| v2 | 190 | Largest. Characters, locations, gods, campaigns, homebrew mechanics. |
| v3 | 38 | Lore, cosmology (World Tree), Ordon. |
| v4 | 63 | Halingo, Ordon. Many empty scaffold notes. |
| V5 | 4 | Scaffold only. |

All four look like successive versions of the same world, so expect overlapping places and gods (Ordon, Halingo, Heresy, Kelemvor, Timeline).
