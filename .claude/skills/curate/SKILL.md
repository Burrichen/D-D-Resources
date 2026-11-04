---
name: curate
description: Turn raw/ material into canonical, deduplicated content/ entries, and keep the repo organised. Use for "review duplicates", "merge", "organise", "clean up", "promote", "what's uncurated", resolving conflicts between vault versions, stale entries after a re-ingest, or any edit to content/.
---

# Curate: raw → canonical content

The goal is **one canonical entry per real thing** (character, place, god, item, rule...) in `content/<type-dir>/<slug>.md`. Each entry cites every raw file it was built from. Other programs read `content/` and `index/`; they never read `raw/`.

## Loop

1. **Survey.** Run `uv run dndres status` (add `-v` to list every uncurated file) and `uv run dndres dupes`, then read `review/duplicates.md` and `review/decisions.md`.
2. **Pick a batch** of related material, for example one duplicate group, one region and its settlements, or one pantheon. Aim for about 5–15 entries. Tell the user what the batch is.
3. **Read every raw file** that describes each thing, across all sources. Use `grep -ril "<name>" raw/` to catch mentions, not only the files with matching titles.
4. **Classify what you find** for each thing:
   - **Same thing, compatible text:** merge into one entry. Keep the most detailed wording, and union the facts.
   - **Same thing, conflicting facts** (name, relationships, dates, alignment, domains, geography, fate, whether it exists at all): **ask the user** (see Conflicts). Never pick silently, even when one vault is newer.
   - **Different things with similar names** (e.g. Khundur vs Khundur (Pre-Destruction), numbered sessions, rule variants): keep them separate, and cross-link them via `related`.
   - **Stubs or empty notes:** don't create an entry for a stub on its own. If the thing matters (other notes reference it), create a `status: draft` entry built from what those references say. Otherwise, list it in your summary as dropped.
5. **Write the entries** (format below).
6. **Check and rebuild:** run `uv run dndres validate` and fix everything it reports, then run `uv run dndres index` and `uv run dndres status`.
7. **Summarise for the user:** entries created or updated, duplicates merged, stubs dropped, and conflicts still open. Don't commit unless they ask.

## Conflicts (the user chose: ask per conflict)

- Before asking, check `review/decisions.md`. A matching earlier decision applies, so don't re-ask.
- Batch conflicts into one AskUserQuestion call with up to 4 questions. Each question is self-contained: thing name, the fact, each version with its source (`v2: …`, `V5: …`).
  - Options are each version, plus "combine", where it makes sense.
  - Put the newest vault first, but do **not** mark it Recommended unless the text gives a real reason.
- **After the answer:**
  - Write the entry.
  - Append to `review/decisions.md`: date, entry id, the question, the choice, and a one-line rationale if one was given.
  - Keep the losing version under `## Earlier versions` in the entry body only if the user asked to.
- **If the user defers:**
  - Write the entry with `status: needs-review`.
  - Use the newest version's facts for now.
  - Add the conflict to `review/conflicts.md`.

## Entry format

Path: `content/<type-dir>/<slug>.md`. The id is `<type>/<slug>`. The schema is `schemas/entry.schema.json`.

```markdown
---
id: deity/kelemvor
type: deity
name: Kelemvor
aliases: [Kelemvor, God of the Dead]
summary: God of the dead who judges souls at the gates of the afterlife.
tags: [pantheon/major, death]
related: [location/the-fugue-plane, character/seneth]
status: canonical
sources:
  - {source: obsidian-dnd-v2, path: "Wiki/Gods/Major/Kelemvor, God of the Dead.md", hash: "sha256:…", role: primary}
  - {source: obsidian-dnd-v3, path: "Lore/Gods and Scions/Scions/Kelemvor.md", hash: "sha256:…", role: merged}
licence: own-work
updated: 2026-11-04
# type-specific fields in snake_case, e.g.:
domains: [death, grave]
alignment: LN
---

Body in plain GitHub-flavoured markdown.
```

### Field rules

- `hash` is copied from the raw file's `_content_hash`. This is what lets `status` detect STALE entries.
- Convert the Obsidian frontmatter that is worth keeping (`Race`, `Alignment`, `AssociatedGroup`, ...) to snake_case fields. Turn values that name other entries into ids in `related`.
- Drop UI-only keys: `NoteIcon`, `cover`, `banner`, `cssclasses`.

### Slugs and types

- The slug is the lowercase-hyphenated name. Keep ids stable: if one must change, add the old name to `aliases` and say so in the summary.
- Types and their directories: character→characters, location→locations, faction→factions, deity→deities, species→species, creature→creatures, item→items (magic items too, with a `rarity` field), spell→spells, mechanic→mechanics (homebrew rules, variant rules, subsystems), table→tables (random tables), lore→lore (concepts, cosmology, history essays), event→events (timeline entries), campaign→campaigns (arcs, session logs), story→stories, misc→misc.

### Converting Obsidian syntax in the body

| Raw syntax | In content |
|---|---|
| `[[Note]]` / `[[Note\|text]]` | `[text](/content/<dir>/<slug>.md)` if the target is curated. Otherwise plain text, and add the target to your "uncurated references" list. |
| `![[Note]]` (note embed) | Inline the relevant text, or link it. |
| `> [!infobox]` callouts | Move the fields into frontmatter; drop the callout. |
| `> [!column]` / `[!info]` / other callouts | Plain markdown sections or blockquotes. |
| `chronos` block | One `event` entry per significant dated item, plus a dated list in the body. |
| `dataview` / `dataviewjs` / `ccard` | Remove. They are live queries. If the query's *result* is meaningful (e.g. "all members of X"), write it out as an explicit list. |
| `statblock` block | Keep as a fenced `statblock` YAML block, which programs can parse. |
| `%% … %%` | Move to a `## GM notes` section. These are often secrets, so don't drop them. |
| `![](/assets/…)` | Keep, and add the path to `images:`. |

## Organisation review (do this when asked, or every ~50 new entries)

- **Overlap check:** run `dupes` again. It also compares canonical entries against each other and against raw files.
- **Folder balance:** if `misc/` has more than about 10 entries, or one type is clearly a mix of two kinds of thing, propose a new type to the user. Changing `schemas/entry.schema.json` and `TYPE_DIRS` needs their approval.
- **Tags:** look for inconsistent tags (`npc` vs `npcs`) and propose a merge.
- **Links:** look for orphan entries (no `related` and nothing links to them) and weak summaries.
- **Scope:** ask the user about out-of-scope material, e.g. v2's `z. Other Games`.

## Never

- Never edit `raw/`, or the user's vaults or docs.
- Never invent lore to fill gaps. A short `draft` is better than a fabricated `canonical` entry.
- Never resolve a substantive conflict without asking.
- Never delete a canonical entry that other programs might reference. Set `status: deprecated` and add `superseded_by: <id>` instead.
