"""Ingest link-shared Google Docs via the public export endpoint.

Tries Markdown export first; falls back to .docx + pandoc. Inline base64 images from
the Markdown export are written out to assets/<source>/<doc-id>/.
"""
from __future__ import annotations

import base64
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import unquote

import httpx

from .common import ASSETS, RawWriter, USER_AGENT, print_stats, sha256, slugify

DOC_ID_RE = re.compile(r"/document/d/([A-Za-z0-9_-]{20,})")
DATA_IMG_RE = re.compile(r"^\[(image\d+)\]:\s*<data:image/(\w+);base64,([^>]+)>\s*$", re.M)


def doc_id(url: str) -> str:
    m = DOC_ID_RE.search(url)
    if not m:
        raise SystemExit(f"Not a Google Docs document URL: {url}")
    return m.group(1)


def _title(resp: httpx.Response, fallback: str) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="([^"]+)"', cd)
    return Path(unquote(m.group(1))).stem if m else fallback


def _export(client: httpx.Client, did: str, fmt: str) -> httpx.Response | None:
    r = client.get(f"https://docs.google.com/document/d/{did}/export", params={"format": fmt})
    if "accounts.google.com" in str(r.url) or r.status_code in (401, 403):
        raise SystemExit(f"Doc {did} is not link-shared. Set sharing to 'Anyone with the link: Viewer'.")
    if r.status_code != 200 or r.headers.get("content-type", "").startswith("text/html"):
        return None
    return r


def ingest(source: dict, *, dry_run: bool = False, urls: list[str] | None = None) -> None:
    urls = urls or source.get("urls", [])
    if dry_run:
        print(f"[{source['id']}] dry run: {len(urls)} docs would be fetched.")
        return
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=120, follow_redirects=True)
    writer = RawWriter(source)
    for url in urls:
        did = doc_id(url)
        asset_dir = ASSETS / source["id"] / did
        r = _export(client, did, "md")
        if r is not None:
            md = r.text
            title = _title(r, did)

            def save_img(m: re.Match) -> str:
                asset_dir.mkdir(parents=True, exist_ok=True)
                name = f"{m.group(1)}.{m.group(2)}"
                (asset_dir / name).write_bytes(base64.b64decode(m.group(3)))
                return f"[{m.group(1)}]: </assets/{source['id']}/{did}/{name}>"

            md = DATA_IMG_RE.sub(save_img, md)
        else:
            r = _export(client, did, "docx")
            if r is None:
                print(f"  could not export {url} (doc not found, or not link-shared); skipped")
                continue
            title = _title(r, did)
            with tempfile.TemporaryDirectory() as tmp:
                docx = Path(tmp) / "doc.docx"
                docx.write_bytes(r.content)
                asset_dir.mkdir(parents=True, exist_ok=True)
                md = subprocess.run(["pandoc", str(docx), "-t", "gfm", "--wrap=none",
                                     f"--extract-media={asset_dir}"],
                                    capture_output=True, text=True, check=True).stdout
            md = md.replace(str(asset_dir), f"/assets/{source['id']}/{did}")
        rel = f"{slugify(title)}--{did[:8]}"
        writer.write(rel, md, content_hash=sha256(md), meta={"title": title, "url": url, "doc_id": did})
    print_stats(source["id"], writer.finish(prune=False))
