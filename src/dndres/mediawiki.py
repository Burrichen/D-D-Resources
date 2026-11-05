"""Ingest pages from a MediaWiki site (e.g. Miraheze) via its api.php.

Infobox templates are lifted into frontmatter (`infobox:`) before conversion, because
pandoc drops templates. Categories become `categories:`. Redirects are not written as
pages; they are collected into raw/<source>/_redirects.json (useful aliases for dedupe).

Private wikis: set `auth_env: NAME` on the source and provide a bot password
(Special:BotPasswords, read-only grant) as NAME_BOT_USER / NAME_BOT_PASS, either in the
environment or in the repo's gitignored `.env` file. Only pages whose content model is
wikitext are ingested (CSS/JS/JSON pages are skipped). Uploaded files are downloaded to
assets/<source>/ unless `download_files: false`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import unquote

import httpx
import mwparserfromhell

from .common import ASSETS, ROOT, RawWriter, USER_AGENT, print_stats, safe_relpath, set_source_field, sha256

BATCH = 50


class Api:
    def __init__(self, url: str):
        self.url = url
        self.client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True)

    def get(self, **params) -> dict:
        params = {"format": "json", "formatversion": 2, "maxlag": 5, **params}
        for attempt in range(5):
            r = self.client.get(self.url, params=params)
            # 429, maxlag, or a transient edge 403 (Miraheze throttles bursts): back off.
            if r.status_code in (429, 403) or "maxlag" in r.text[:200]:
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                raise SystemExit(f"API error: {data['error']}")
            return data
        raise SystemExit("API kept rate-limiting; try again later.")

    def login(self, prefix: str) -> None:
        user, password = _secret(f"{prefix}_BOT_USER"), _secret(f"{prefix}_BOT_PASS")
        if not (user and password):
            raise SystemExit(f"This source needs a bot password: set {prefix}_BOT_USER and {prefix}_BOT_PASS "
                             "in the environment or in .env (create one at Special:BotPasswords).")
        token = self.get(action="query", meta="tokens", type="login")["query"]["tokens"]["logintoken"]
        r = self.client.post(self.url, data={"action": "login", "lgname": user, "lgpassword": password,
                                             "lgtoken": token, "format": "json", "formatversion": 2})
        r.raise_for_status()
        result = r.json().get("login", {})
        if result.get("result") != "Success":
            raise SystemExit(f"Login failed: {result.get('result')} {result.get('reason', '')}".strip())

    def iterate(self, list_name: str, **params):
        cont: dict = {}
        while True:
            data = self.get(action="query", list=list_name, **params, **cont)
            yield from data["query"][list_name]
            if "continue" not in data:
                return
            cont = data["continue"]
            time.sleep(0.3)


def _secret(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name:
                return v.strip().strip('"').strip("'")
    return None


def _titles(api: Api, source: dict) -> list[str]:
    pages = source.get("pages", "all")
    ns = "|".join(str(n) for n in source.get("namespaces", [0]))
    if pages == "all":
        # allpages takes a single namespace per query
        return [p["title"] for n in source.get("namespaces", [0])
                for p in api.iterate("allpages", apnamespace=n, aplimit="max")]
    if isinstance(pages, dict) and "category" in pages:
        cat = pages["category"]
        cat = cat if cat.startswith("Category:") else f"Category:{cat}"
        return [p["title"] for p in api.iterate("categorymembers", cmtitle=cat, cmnamespace=ns, cmlimit="max")]
    if isinstance(pages, list):
        return pages
    raise SystemExit("`pages` must be 'all', a list of titles, or {category: Name}.")


_TAG_FLAGS = re.I | re.S
_SWITCH_RE = re.compile(r"__[A-Z]+__")
_STYLE_TAGS_RE = re.compile(r"<templatestyles[^>]*/?>|</?(?:includeonly|noinclude|onlyinclude|choose)[^>]*>", re.I)
_CELL_RE = re.compile(r"<(th|td)([^>]*)>(.*?)</\1>", _TAG_FLAGS)
_TITLE_DIV_RE = re.compile(r'<div[^>]*class="[^"]*-title"[^>]*>\s*([^<\n][^<]*?)\s*</div>', re.I)


def _html_tables_to_wikitext(text: str) -> str:
    """Rewrite simple HTML tables as wikitable syntax so pandoc emits markdown tables."""
    def table(m: re.Match) -> str:
        out = ["{|" + m.group(1)]
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(2), _TAG_FLAGS):
            out.append("|-")
            for tag, cattrs, cell in _CELL_RE.findall(row):
                cell, cattrs = " ".join(cell.split()), cattrs.strip()
                out.append(("!" if tag.lower() == "th" else "|") + (f" {cattrs} |" if cattrs else "") + f" {cell}")
        out.append("|}")
        return "\n" + "\n".join(out) + "\n"
    return re.sub(r"<table([^>]*)>(.*?)</table>", table, text, flags=_TAG_FLAGS)


def _cell_value(line: str) -> str:
    body = line[1:]
    # strip a leading attribute block:  ! style="..." | Value
    first = body.split("|", 1)[0]
    if "|" in body and "[[" not in first and "=" in first:
        body = body.split("|", 1)[1]
    return body.strip()


def _lift_infobox(text: str) -> tuple[dict | None, str]:
    """Take the first sidebar-style key/value wikitable out of the page.

    It counts as an infobox when the table floats right, has an infobox/data class, or
    sits just inside an infobox div. Non key/value rows (usually the image) stay in the text.
    """
    for m in re.finditer(r"^\{\|(.*?)^\|\}", text, re.M | re.S):
        head, _, rows = m.group(1).partition("\n")
        before = text[max(0, m.start() - 600):m.start()]
        if not (re.search(r"float\s*:\s*right|infobox|-data\b", head, re.I) or "infobox" in before):
            continue
        params: dict[str, str] = {}
        title, keep = None, []
        for row in re.split(r"^\|-.*$", rows, flags=re.M):
            cells = [ln.strip() for ln in row.strip().splitlines() if ln.strip()]
            if cells and cells[0].startswith("|+"):
                title = _cell_value(cells.pop(0)[1:])
            heads = [c for c in cells if c.startswith("!")]
            datas = [c for c in cells if c.startswith("|")]
            if len(heads) == 1 and len(datas) == 1:
                key = mwparserfromhell.parse(_cell_value(heads[0])).strip_code().strip()
                val = mwparserfromhell.parse(_cell_value(datas[0])).strip_code().strip()
                if key and val:
                    params[key] = val
            else:
                keep += [_cell_value(c) for c in cells]
        if len(params) < 2:
            continue
        box: dict = {"template": "table", "params": params}
        if title:
            box["title"] = mwparserfromhell.parse(title).strip_code().strip()
        return box, text[:m.start()] + "\n\n".join(keep) + text[m.end():]
    return None, text


def _gallery(m: re.Match) -> str:
    out = []
    for line in m.group(1).splitlines():
        name, _, caption = line.strip().partition("|")
        if name:
            name = name if name.lower().startswith(("file:", "image:")) else f"File:{name}"
            out.append(f"[[{name}|frameless|{caption.strip() or name.split(':', 1)[1]}]]")
            if caption.strip():
                out.append(f"''{caption.strip()}''")
    return "\n\n" + "\n\n".join(out) + "\n\n"


def _preclean(text: str) -> str:
    text = re.sub(r"<gallery[^>]*>(.*?)</gallery>", _gallery, text, flags=_TAG_FLAGS)
    text = _STYLE_TAGS_RE.sub("", text)
    text = _SWITCH_RE.sub("", text)
    text = re.sub(r"<option[^>]*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</option>", "\n\n----\n\n", text, flags=re.I)
    text = _TITLE_DIV_RE.sub(lambda m: "\n\n'''" + m.group(1).strip() + "'''\n\n", text)
    text = re.sub(r"<h([1-6])[^>]*>\s*(.*?)\s*</h\1>",
                  lambda m: "\n\n" + "=" * int(m.group(1)) + f" {m.group(2)} " + "=" * int(m.group(1)) + "\n\n",
                  text, flags=_TAG_FLAGS)
    text = re.sub(r"</?div[^>]*>", "\n\n", text, flags=re.I)          # layout wrappers
    text = re.sub(r"</?(?:span|small|big|font|center)[^>]*>", "", text, flags=re.I)
    return _html_tables_to_wikitext(text)


def _expand_templates(wikitext: str, title: str, templates: dict[str, str], depth: int = 3) -> str:
    """Substitute calls to this wiki's own templates that pass parameters.

    Many Miraheze pages are a single {{Layout | intro = ... | overview = ...}} call, so the
    content lives in the parameters. Expanding against the template's wikitext keeps it.
    Parameterless templates (quote boxes, navboxes) are left for convert() to drop.
    """
    code = mwparserfromhell.parse(wikitext)
    changed = False
    for tpl in code.filter_templates(recursive=False):
        name = str(tpl.name).strip()
        key = name[:1].upper() + name[1:].replace("_", " ")
        body = templates.get(key)
        if body is None or not tpl.params:
            continue
        params = {str(p.name).strip(): str(p.value).strip() for p in tpl.params}
        body = re.sub(r"<noinclude>.*?</noinclude>", "", body, flags=_TAG_FLAGS)
        body = re.sub(r"</?(?:includeonly|onlyinclude)>", "", body, flags=re.I)
        t = mwparserfromhell.parse(body)
        for arg in t.filter_arguments():          # recursive: args sit inside <div>s
            pname = str(arg.name).strip()
            value = params.get(pname)
            if value is None:
                value = str(arg.default) if arg.default is not None else ""
            try:
                t.replace(arg, value)
            except ValueError:                     # already replaced along with a parent
                pass
        expanded = re.sub(r"\{\{\s*PAGENAME\s*\}\}", title, str(t))
        # leftover {{{x|default}}} nested in defaults
        expanded = re.sub(r"\{\{\{[^|{}]+\|([^{}]*)\}\}\}", r"\1", expanded)
        expanded = re.sub(r"\{\{\{[^{}]*\}\}\}", "", expanded)
        code.replace(tpl, expanded)
        changed = True
    out = str(code)
    return _expand_templates(out, title, templates, depth - 1) if changed and depth > 1 else out


def convert(wikitext: str, *, title: str = "", templates: dict[str, str] | None = None) -> tuple[dict, str]:
    meta: dict = {}
    infoboxes = []
    dropped = set()
    if templates:
        wikitext = _expand_templates(wikitext, title, templates)
    code = mwparserfromhell.parse(_preclean(wikitext))
    for tpl in code.filter_templates(recursive=False):
        name = str(tpl.name).strip()
        if name.upper().startswith("DISPLAYTITLE:"):
            meta["display_title"] = name.split(":", 1)[1].strip()
            code.remove(tpl)
        elif "infobox" in name.lower() or name.lower().startswith(("character", "location", "deity", "npc")):
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
    text = str(code)
    if not infoboxes:
        box, text = _lift_infobox(text)
        if box:
            infoboxes.append(box)
    if infoboxes:
        meta["infobox"] = infoboxes[0] if len(infoboxes) == 1 else infoboxes
    if cats:
        meta["categories"] = cats
    if dropped:
        meta["templates_dropped"] = sorted(dropped)
    # -raw_html: layout <div>/<span> wrappers are unwrapped (content kept); figures become ![]().
    md = subprocess.run(["pandoc", "-f", "mediawiki", "-t", "gfm-raw_html+wikilinks_title_after_pipe", "--wrap=none"],
                        input=text, capture_output=True, text=True, check=True).stdout
    return meta, re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


def _list_files(api: Api, source: dict) -> list[dict]:
    """[{name, url, sha1, dest, link}] for every uploaded file."""
    root = ASSETS / source["id"]
    out = []
    for img in api.iterate("allimages", aiprop="url|sha1", ailimit="max"):
        dest = root / safe_relpath(img["name"])
        out.append({**img, "dest": dest, "link": f"/assets/{source['id']}/{dest.name}"})
    return out


def _download_files(api: Api, files: list[dict]) -> list[str]:
    """Fetch files into assets/; return names that are still missing.

    A private wiki's img_auth.php rejects bot-password sessions, so on the first refusal we
    stop asking rather than hammering it. Missing files can be dropped into assets/ by hand;
    page links already point there.
    """
    missing, refused = [], False
    for f in files:
        dest: Path = f["dest"]
        if dest.exists() and hashlib.sha1(dest.read_bytes()).hexdigest() == f.get("sha1"):
            continue
        if not refused:
            r = api.client.get(f["url"])
            time.sleep(0.3)
            if r.status_code == 200:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                continue
            refused = True
        if not dest.exists():
            missing.append(f["name"])
    return missing


_IMG_RE = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)")


def _link_files(md: str, files: dict[str, str]) -> str:
    def sub(m: re.Match) -> str:
        target = unquote(m.group(2)).replace("_", " ")
        target = target.split(":", 1)[1] if target.lower().startswith(("file:", "image:")) else target
        return m.group(1) + files.get(target, files.get(target[:1].upper() + target[1:], m.group(2)))
    return _IMG_RE.sub(sub, md)


def _load_templates(api: Api) -> dict[str, str]:
    """{Template name (no prefix) -> wikitext} for every wikitext page in the Template namespace."""
    names = [p["title"] for p in api.iterate("allpages", apnamespace=10, aplimit="max")]
    out: dict[str, str] = {}
    for i in range(0, len(names), BATCH):
        data = api.get(action="query", prop="revisions", rvprop="content|contentmodel", rvslots="main",
                       titles="|".join(names[i:i + BATCH]))
        for page in data["query"].get("pages", []):
            slot = (page.get("revisions") or [{}])[0].get("slots", {}).get("main", {})
            if slot.get("contentmodel") == "wikitext":
                out[page["title"].split(":", 1)[1]] = slot.get("content", "")
    return out


def ingest(source: dict, *, dry_run: bool = False) -> None:
    api = Api(source["api"])
    if source.get("auth_env"):
        api.login(source["auth_env"])
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
    file_list = _list_files(api, source) if source.get("download_files", True) else []
    files = {f["name"].replace("_", " "): f["link"] for f in file_list}
    templates = _load_templates(api)
    writer = RawWriter(source)
    skipped: list[str] = []
    redirects: dict[str, str] = {}
    for i in range(0, len(titles), BATCH):
        chunk = titles[i:i + BATCH]
        data = api.get(action="query", prop="revisions", rvprop="content|ids|timestamp|contentmodel",
                       rvslots="main", titles="|".join(chunk))
        for page in data["query"].get("pages", []):
            if page.get("missing") or not page.get("revisions"):
                continue
            rev = page["revisions"][0]
            slot = rev["slots"]["main"]
            if slot.get("contentmodel", "wikitext") != "wikitext":
                skipped.append(page["title"])
                continue
            text = slot.get("content", "")
            if not text.strip():
                continue
            if text.lstrip().upper().startswith("#REDIRECT"):
                target = mwparserfromhell.parse(text).filter_wikilinks()
                if target:
                    redirects[page["title"]] = str(target[0].title).strip()
                continue
            meta, md = convert(text, title=page["title"], templates=templates)
            md = _link_files(md, files)
            rel = "/".join(safe_relpath(part) for part in page["title"].replace(":", "/", 1).split("/"))
            writer.write(rel, f"# {page['title']}\n\n{md}", content_hash=sha256(text),
                         original_fm=meta, meta={
                             "title": page["title"],
                             "url": f"{base}/wiki/{page['title'].replace(' ', '_')}",
                             "revid": rev.get("revid"), "revised": rev.get("timestamp")})
        time.sleep(0.5)
    missing_files = _download_files(api, file_list)
    (writer.dir / "_redirects.json").write_text(json.dumps(redirects, indent=1, ensure_ascii=False))
    print_stats(source["id"], writer.finish())
    print(f"  redirects recorded: {len(redirects)}")
    print(f"  files linked: {len(files)}, present in assets/: {len(files) - len(missing_files)}")
    if missing_files:
        print(f"  could not download (add by hand to assets/{source['id']}/): {', '.join(missing_files)}")
    if skipped:
        print(f"  skipped non-wikitext pages: {', '.join(skipped)}")
