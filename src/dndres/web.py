"""Ingest arbitrary web pages: fetch politely (robots.txt), extract main content to markdown."""
from __future__ import annotations

import time
import urllib.robotparser
from urllib.parse import urlparse

import httpx
import trafilatura

from .common import RawWriter, USER_AGENT, print_stats, safe_relpath, sha256, slugify

_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


def _allowed(client: httpx.Client, url: str) -> bool:
    u = urlparse(url)
    key = f"{u.scheme}://{u.netloc}"
    if key not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = client.get(f"{key}/robots.txt")
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except httpx.HTTPError:
            rp.parse([])
        _robots[key] = rp
    return _robots[key].can_fetch(USER_AGENT, url)


def _metadata(html: str, url: str) -> dict:
    doc = trafilatura.bare_extraction(html, url=url, with_metadata=True)
    if doc is None:
        return {}
    d = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc)
    return {k: d.get(k) for k in ("title", "author", "date", "sitename") if d.get(k)}


def ingest(source: dict, *, dry_run: bool = False, urls: list[str] | None = None) -> None:
    urls = urls or source.get("urls", [])
    if dry_run:
        print(f"[{source['id']}] dry run: {len(urls)} urls would be fetched.")
        return
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True)
    writer = RawWriter(source)
    for url in urls:
        if not _allowed(client, url):
            print(f"  robots.txt disallows {url}; skipped")
            continue
        r = client.get(url)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code} for {url}; skipped")
            continue
        md = trafilatura.extract(r.text, url=url, output_format="markdown", include_tables=True,
                                 include_links=True, include_images=True, include_formatting=True)
        if not md:
            print(f"  no main content extracted from {url}; skipped")
            continue
        meta = _metadata(r.text, url)
        u = urlparse(url)
        rel = f"{safe_relpath(u.netloc)}/{slugify(u.path + ('-' + u.query if u.query else '')) or 'index'}"
        title = meta.pop("title", None) or rel
        writer.write(rel, f"# {title}\n\n{md}", content_hash=sha256(md), original_fm=meta,
                     meta={"title": title, "url": url})
        time.sleep(1)
    # Web sources are often ingested incrementally (one URL at a time), so never prune.
    print_stats(source["id"], writer.finish(prune=False))
