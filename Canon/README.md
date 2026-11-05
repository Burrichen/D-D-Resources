# Canon

The lore of the world of Kurovia. Anything in this folder is canon. It is the final, trusted version, and it outranks anything in `raw/` or `content/` that disagrees with it. Other projects reference this folder directly.

Where it sits in the flow (full diagram in [CLAUDE.md](../CLAUDE.md)):

```
raw/  ──curate──▶  content/  ──promote──▶  Canon/
(as imported)      (cleaned)               (Kurovia lore, final)
```

## What belongs here

Kurovia world lore: characters, locations, factions, deities, species, creatures, items, events, lore and stories.

These stay in `content/` and don't come here: mechanics, random tables, spells, campaign and session logs, `misc`, and anything borrowed from published D&D (for example Kelemvor or Tyr).

## Layout

```
Canon/
  characters/<slug>.md
  locations/<slug>.md
  factions/<slug>.md
  deities/<slug>.md
  species/<slug>.md
  creatures/<slug>.md
  items/<slug>.md
  events/<slug>.md
  lore/<slug>.md
  stories/<slug>.md
```

- One file per thing. One folder level, named by type. No other subfolders.
- Each file has the same frontmatter as a `content/` entry (id, name, aliases, summary, related, sources...), so its id, such as `location/ordon`, is the same as when it was in `content/`.
- The body is plain markdown: no Obsidian syntax, no Dataview, no template leftovers.

## How things get here

1. An entry is cleaned up in `content/` and marked `status: canonical`, with no open duplicates or conflicts.
2. Claude proposes a batch to promote, and you approve it.
3. Each approved file is **moved** from `content/` to `Canon/`. It is never copied, so there is only ever one version of each thing.

Nothing in here is changed without your approval, not even typo fixes. If you write a file here by hand, it's canon as written.
