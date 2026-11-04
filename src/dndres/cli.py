"""dndres - command line entry point. Run `uv run dndres --help`."""
from __future__ import annotations

import argparse
import sys

from . import curate
from .common import get_source, load_sources

INGESTERS = {"obsidian": "obsidian", "mediawiki": "mediawiki", "web": "web", "gdoc": "gdocs"}


def _ingest(source: dict, dry_run: bool, urls: list[str] | None) -> None:
    mod_name = INGESTERS.get(source["type"])
    if not mod_name:
        raise SystemExit(f"No ingester for type '{source['type']}'")
    mod = __import__(f"dndres.{mod_name}", fromlist=["ingest"])
    kwargs = {"dry_run": dry_run}
    if urls:
        if source["type"] not in ("web", "gdoc"):
            raise SystemExit("--url only applies to web and gdoc sources")
        kwargs["urls"] = urls
    mod.ingest(source, **kwargs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dndres", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sources", help="list registered sources")

    p = sub.add_parser("ingest", help="pull a source into raw/")
    p.add_argument("source", nargs="?", help="source id from sources.yaml")
    p.add_argument("--all", action="store_true", help="ingest every registered source")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--url", action="append", help="(web/gdoc) ingest just this URL; repeatable")

    p = sub.add_parser("status", help="what's uncurated / stale / orphaned")
    p.add_argument("-v", "--verbose", action="store_true", help="list every uncurated raw file")

    p = sub.add_parser("dupes", help="write review/duplicates.md")
    p.add_argument("--title-threshold", type=int, default=90)
    p.add_argument("--body-threshold", type=int, default=80)

    sub.add_parser("validate", help="check content/ against schema and link rules")
    sub.add_parser("index", help="rebuild index/manifest.json and index/entries.jsonl")

    a = ap.parse_args(argv)
    if a.cmd == "sources":
        for s in load_sources():
            print(f"{s['id']:28} {s['type']:10} last_pulled={s.get('last_pulled')}")
    elif a.cmd == "ingest":
        if a.all:
            for s in load_sources():
                _ingest(s, a.dry_run, None)
        elif a.source:
            _ingest(get_source(a.source), a.dry_run, a.url)
        else:
            ap.error("give a source id or --all")
    elif a.cmd == "status":
        curate.status(a.verbose)
    elif a.cmd == "dupes":
        curate.dupes(a.title_threshold, a.body_threshold)
    elif a.cmd == "validate":
        return curate.validate()
    elif a.cmd == "index":
        curate.build_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
