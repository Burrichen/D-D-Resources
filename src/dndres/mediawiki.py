"""Ingest pages from a MediaWiki site (e.g. Miraheze) via its api.php.

Infobox templates are lifted into frontmatter (`infobox:`) before conversion, because
pandoc drops templates. Categories become `categories:`. Redirects are not written as
pages; they are collected into raw/<source>/_redirects.json (useful aliases for dedupe).
"""
from __future__ import annotations

import json
import subprocess
import time

import httpx
import mwparserfromhell

from .common import RawWriter, USER_AGENT, print_stats, safe_relpath, set_source_field, sha256

BATCH = 50


class Api:
    def __init__(self, url: str):
        self.url = url
        self.client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True)

    def get(self, **params) -> dict:
        params = {"format": "json", "formatversion": 2, "maxlag": 5, **params}
        for attempt in range(5):
            r = self.client.get(self.url, params=params)
            if r.status_code == 429 or "maxlag" in r.text[:200]:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise SystemExit(f"API error: {data['error']}")
            return data
        raise SystemExit("API kept rate-limiting; try again later.")

    def iterate(self, list_name: str, **params):
        cont: dict = {}
        while True:
            data = self.get(action="query", list=list_name, **params, **cont)
            yield from data["query"][list_name]
            if "continue" not in data:
                return
            cont = data["continue"]
            time.sleep(0.3)


def _titles(api: Api, source: dict) -> list[str]:
    pages = source.get("pages", "all")
    ns = "|".join(str(n) for n in source.get("namespaces", [0]))
    if pages == "all":
        return [p["title"] for p in api.iterate("allpages", apnamespace=ns, aplimit="max")]
    if isinstance(pages, dict) and "category" in pages:
        cat = pages["category"]
        cat = cat if cat.startswith("Category:") else f"Category:{cat}"
        return [p["title"] for p in api.iterate("categorymembers", cmtitle=cat, cmnamespace=ns, cmlimit="max")]
    if isinstance(pages, list):
        return pages
    raise SystemExit("`pages` must be 'all', a list of titles, or {category: Name}.")


def convert(wikitext: str) -> tuple[dict, str]:
    code = mwparserfromhell.parse(wikitext)
    meta: dict = {}
    infoboxes = []
    dropped = set()
    for tpl in code.filter_templates(recursive=False):
        name = str(tpl.name).strip()
        if "infobox" in name.lower() or name.lower().startswith(("character", "location", "deity", "npc")):
            infoboxes.append({"template": name, "params": {
                str(p.name).strip(): mwparserfromhell.parse(str(p.value)).strip_code().strip()
                for p in tpl.params if str(p.value).strip()}})
            code.remove(tpl)
        else:
            dropped.add(name)
    cats = []
    for link in code.filter_wikilinks():
        t = str(link.title).strip()
        if t.lower().startswith("category:"):
            cats.append(t.split(":", 1)[1].strip())
            code.remove(link)
    if infoboxes:
        meta["infobox"] = infoboxes[0] if len(infoboxes) == 1 else infoboxes
    if cats:
        meta["categories"] = cats
    if dropped:
        meta["templates_dropped"] = sorted(dropped)
    md = subprocess.run(["pandoc", "-f", "mediawiki", "-t", "gfm+wikilinks_title_after_pipe", "--wrap=none"],
                        input=str(code), capture_output=True, text=True, check=True).stdout
    return meta, md


def ingest(source: dict, *, dry_run: bool = False) -> None:
    api = Api(source["api"])
    if not source.get("licence"):
        info = api.get(action="query", meta="siteinfo", siprop="rightsinfo")
        lic = info["query"]["rightsinfo"].get("text") or "unknown"
        source["licence"] = lic
        if not dry_run:
            set_source_field(source["id"], "licence", lic)

    titles = _titles(api, source)
    if dry_run:
        print(f"[{source['id']}] dry run: {len(titles)} pages would be fetched.")
        return
    base = source["api"].rsplit("/w/api.php", 1)[0].rsplit("/api.php", 1)[0]
    writer = RawWriter(source)
    redirects: dict[str, str] = {}
    for i in range(0, len(titles), BATCH):
        chunk = titles[i:i + BATCH]
        data = api.get(action="query", prop="revisions", rvprop="content|ids|timestamp",
                       rvslots="main", titles="|".join(chunk))
        for page in data["query"].get("pages", []):
            if page.get("missing") or not page.get("revisions"):
                continue
            rev = page["revisions"][0]
            text = rev["slots"]["main"].get("content", "")
            if text.lstrip().upper().startswith("#REDIRECT"):
                target = mwparserfromhell.parse(text).filter_wikilinks()
                if target:
                    redirects[page["title"]] = str(target[0].title).strip()
                continue
            meta, md = convert(text)
            rel = "/".join(safe_relpath(part) for part in page["title"].replace(":", "/", 1).split("/"))
            writer.write(rel, f"# {page['title']}\n\n{md}", content_hash=sha256(text),
                         original_fm=meta, meta={
                             "title": page["title"],
                             "url": f"{base}/wiki/{page['title'].replace(' ', '_')}",
                             "revid": rev.get("revid"), "revised": rev.get("timestamp")})
        time.sleep(0.5)
    (writer.dir / "_redirects.json").write_text(json.dumps(redirects, indent=1, ensure_ascii=False))
    print_stats(source["id"], writer.finish())
    print(f"  redirects recorded: {len(redirects)}")
