#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
from pathlib import Path

SECRET_KEY = re.compile(r"(secret|token|key|password|passwd|pwd|credential)", re.I)
HIGH_ENTROPY = re.compile(r"[A-Za-z0-9_=-]{24,}")
TOKEN_SHAPE = re.compile(r"(TEST_TOKEN_PLACEHOLDER|EXAMPLE_SECRET|password123)")

def should_read(path: Path) -> bool:
    name=path.name
    if name.endswith(".env.example"):
        return False
    return name == ".env" or name.endswith(".env")

def transform(path):
    if not should_read(Path(path)):
        raise ValueError("input must be .env or *.env, not .env.example")
    lines=Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    out=[]; flagged=[]
    for line in lines:
        stripped=line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line); continue
        m=re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            out.append(line); continue
        key,value=m.group(1),m.group(2)
        clean=value.strip().strip('"').strip("'")
        if SECRET_KEY.search(key) or HIGH_ENTROPY.fullmatch(clean) or TOKEN_SHAPE.search(clean):
            flagged.append(key)
        out.append(f"{key}=")
    return "\n".join(out).rstrip()+"\n", flagged

def render(path):
    content, flagged=transform(path)
    if flagged:
        content += "\n# Secret-looking keys to review: " + ", ".join(sorted(set(flagged))) + "\n"
    return content

def main():
    ap=argparse.ArgumentParser(description="Create a safe .env.example from .env.")
    ap.add_argument("path", nargs="?", default=".env")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--output", default=".env.example")
    args=ap.parse_args()
    content=render(args.path)
    if args.write:
        out=Path(args.output)
        if out.exists() and not args.force:
            raise SystemExit("target exists; pass --force to overwrite")
        out.write_text(content, encoding="utf-8", newline="\n")
    else:
        print(content, end="")
if __name__=="__main__": main()
