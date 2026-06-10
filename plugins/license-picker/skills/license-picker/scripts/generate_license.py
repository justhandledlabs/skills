#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICENSE_DIR = ROOT / "references" / "licenses"
ALIASES = {"mit":"mit", "apache":"apache-2.0", "apache-2.0":"apache-2.0", "bsd-3":"bsd-3-clause", "bsd-3-clause":"bsd-3-clause", "bsd-2":"bsd-2-clause", "bsd-2-clause":"bsd-2-clause", "gpl-3.0":"gpl-3.0", "gpl3":"gpl-3.0", "mpl-2.0":"mpl-2.0", "mpl2":"mpl-2.0", "unlicense":"unlicense"}

def supported_ids():
    return sorted(set(ALIASES.values()))

def render(license_id, holder, year):
    key = ALIASES.get(license_id.lower())
    if not key:
        return None
    template = (LICENSE_DIR / f"{key}.txt").read_text(encoding="utf-8")
    return template.replace("{holder}", holder).replace("{year}", str(year)).rstrip() + "\n"

def main():
    ap=argparse.ArgumentParser(description="Generate a LICENSE file from bundled templates.")
    ap.add_argument("--license", required=False)
    ap.add_argument("--holder", required=False)
    ap.add_argument("--year", required=False)
    ap.add_argument("--input-json")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--output", default="LICENSE")
    args=ap.parse_args()
    data={}
    if args.input_json:
        data=json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    license_id=args.license or data.get("license")
    holder=args.holder or data.get("holder")
    year=args.year or data.get("year")
    if not license_id or not holder or not year:
        raise SystemExit("required: --license, --holder, --year")
    text=render(license_id, holder, year)
    if text is None:
        print("Supported license ids: " + ", ".join(supported_ids()))
        return
    if args.write:
        out=Path(args.output)
        if out.exists() and not args.force:
            raise SystemExit("target exists; pass --force to overwrite")
        out.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
if __name__=="__main__":
    main()
