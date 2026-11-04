---
name: ingest-wiki-web
description: Pull pages from a Miraheze (or any MediaWiki) wiki, or from ordinary web pages, into this repo's raw/ store with provenance and licence. Use when the user gives a miraheze.org / fandom / MediaWiki URL, a category of wiki pages, or a web page about D&D content to import.
---

# Ingest from MediaWiki (Miraheze) or the web

## MediaWiki / Miraheze

1. **Find the API.** For Miraheze it is `https://<wiki>.miraheze.org/w/api.php`. Custom domains also usually use `/w/api.php`. Confirm with `curl -s '<api>?action=query&meta=siteinfo&format=json' | head -c 300`.
2. **Agree the scope with the user** before pulling a whole wiki:
   - `pages: all` takes every page in `namespaces` (default `[0]`, the main namespace).
   - `pages: {category: Gods}` takes the members of one category.
   - `pages: [Title A, Title B]` takes an explicit list.
3. **Register** in `sources.yaml` with `id: miraheze-<wiki>` (or `mediawiki-<site>`), `type: mediawiki`, `api`, `pages`, `priority`, and `licence: ""`. A blank licence is auto-filled from the wiki's siteinfo, which is usually CC BY-SA on Miraheze.
4. Run `uv run dndres ingest <id> --dry-run`. If it reports more than about 300 pages, confirm with the user before running it for real.
5. Run `uv run dndres ingest <id>`.
6. **Check the conversion:**
   - Infobox-like templates are lifted into frontmatter as `infobox:`.
   - Other templates are dropped and listed in `templates_dropped`.
   - If an important template, such as a statblock template, shows up in `templates_dropped`, tell the user, and add its name to the infobox heuristic in `src/dndres/mediawiki.py` (`convert()`).
   - Redirects go to `raw/<id>/_redirects.json`. These are aliases, and `curate` should use them.
7. Run `uv run dndres dupes`, then report.

## Web pages

1. Register a `type: web` source per site or topic, e.g. `id: web-<site>`. Then either list `urls:`, or add pages one at a time with `uv run dndres ingest <id> --url <URL>` (repeatable). Web sources are never pruned, so URLs accumulate.
2. **Licence.** Ask the user, or record what the site states:
   - SRD / Creative Commons content (e.g. the 5.1/5.2 SRD): record the exact licence.
   - Official non-SRD content (D&D Beyond, published books) and other people's homebrew: record `licence: "proprietary - personal reference only"`, so that consumer programs can filter it out of anything they publish.
3. Pages where robots.txt disallows fetching are skipped. Do not try to work around this.
4. If extraction returns nothing (JS-rendered page), tell the user. Do not paste page content into `raw/` by hand.

## Rules

- Generic User-Agent only. Never put the user's email in requests.
- Be polite: the code already rate-limits. Don't parallelise ingests against one host.
- Never edit `raw/` by hand.
