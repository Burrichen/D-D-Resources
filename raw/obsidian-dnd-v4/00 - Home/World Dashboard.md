---
_source: obsidian-dnd-v4
_source_path: 00 - Home/World Dashboard.md
_title: World Dashboard
_licence: own-work
_fetched: '2026-11-04T10:54:34+00:00'
_content_hash: sha256:1698a19207aeaab0e5e21dceda0e6846b229969b8e0a3a59c6ed69c7353dd3bf
---

![[99 - Assets/Handouts/dashboard-banner.png]]

# World Dashboard
*Lore, mechanics, references, and current work*

> [!abstract] Quick Links
> - [[World]]
> - [[Places]]
> - [[NPCs]]
> - [[Factions]]
> - [[Lore]]
> - [[Stories]]
> - [[D&D Core Rules]]
> - [[Homebrew]]
> - [[Magic Items]]
> - [[Third Party Content]]
> - [[Glossary]]
> - [[Timeline]]

> [!todo] Dashboard To-Do
> - [ ] Refine To-Do Board
> - [ ] Find Cover Images
> - [ ] Import DND Content
> - [ ] Send over notes
> - [ ] Import Alex images / images


## Recently Edited

```dataview
LIST file.link
WHERE file.path != this.file.path
AND !contains(file.folder, "99 - Assets")
SORT file.mtime DESC
LIMIT 5
```
## Quote of the Day

```dataviewjs
const quotes = dv.pages('"07 - References/Texts + Quotes"')
  .where(p => p.quote)
  .array();

if (quotes.length === 0) {
  dv.paragraph("Add quote notes with a `quote` property to see a daily quote here.");
} else {
  const today = new Date();
  const seed = `${today.getFullYear()}-${today.getMonth() + 1}-${today.getDate()}`;

  let hash = 0;
  for (const ch of seed) {
    hash = ((hash << 5) - hash) + ch.charCodeAt(0);
    hash |= 0;
  }

  const q = quotes[Math.abs(hash) % quotes.length];
  dv.paragraph(`> ${q.quote}`);
  dv.paragraph(q.source ? `— ${q.source}` : `— ${q.file.link}`);
}
```
## Random Page

```dataviewjs
const loreFolders = [
  "01 - World",
  "02 - People",
  "03 - Groups",
  "04 - Lore",
  "05 - Stories/Legends",
  "05 - Stories/Short Stories"
];

const pages = dv.pages()
  .where(p => loreFolders.some(f => p.file.path.startsWith(f + "/")))
  .array();

if (pages.length === 0) {
  dv.paragraph("Add some lore notes first.");
} else {
  const pick = pages[Math.floor(Math.random() * pages.length)];
  dv.paragraph(`**Open:** ${pick.file.link}`);
  dv.paragraph("*Reload the note to reroll.*");
}
```

## World
- [[World]]
- [[Places]]
- [[Regions]]
- [[Landmarks]]
- [[People]]
- [[NPCs]]
- [[Players]]
- [[Dynasties]]
- [[Groups]]
- [[Factions]]
- [[Guilds]]
- [[Religions]]
- [[Lore]]
- [[Stories]]

## Mechanics
- [[D&D Core Rules]]
- [[Homebrew]]
- [[Magic Items]]
- [[Third Party Content]]

## References
- [[Glossary]]
- [[Texts + Quotes]]
- [[Timeline]]
- [[Images]]