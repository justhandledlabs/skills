#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

EXTENSIONS={".py",".js",".ts",".jsx",".tsx",".go",".java",".rb",".php",".c",".cpp",".cs",".rs",".md"}
IGNORE_DIRS={"node_modules",".git","dist","build","vendor","__pycache__"}
TAGS=[("TDE001","TODO"),("TDE002","FIXME"),("TDE003","HACK"),("TDE004","XXX"),("TDE005","BUG"),("TDE006","OPTIMIZE")]
PATTERN=re.compile(r"\b("+"|".join(re.escape(t) for _,t in TAGS)+r")\b\s*:?[ \t]*(.*)", re.I)
CODE_BY_TAG={tag:code for code,tag in TAGS}

def should_read(path: Path)->bool:
    return path.suffix.lower() in EXTENSIONS

def iter_files(paths):
    for raw in paths:
        p=Path(raw)
        if not p.exists(): yield p,"","missing"; continue
        if p.is_file():
            if should_read(p): yield p,p.read_text(encoding="utf-8",errors="replace"),None
            continue
        for child in p.rglob("*"):
            if child.is_file() and should_read(child) and not any(part in IGNORE_DIRS for part in child.parts):
                yield child,child.read_text(encoding="utf-8",errors="replace"),None

def scan(paths):
    findings=[]; missing=[]; scanned=0; counts={tag:0 for _,tag in TAGS}
    for path,text,error in iter_files(paths):
        if error: missing.append(str(path)); continue
        scanned+=1
        for lineno,line in enumerate(text.splitlines(),1):
            m=PATTERN.search(line)
            if m:
                tag=m.group(1).upper(); counts[tag]+=1
                findings.append({"code":CODE_BY_TAG[tag],"severity":"info","file":str(path),"line":lineno,"tag":tag,"message":f"{tag} comment found.","excerpt":m.group(2).strip()})
    return {"scanner":"todo-fixme-extractor","files_scanned":scanned,"missing_paths":missing,"counts":counts,"findings":findings}

def print_markdown(result):
    print("# TODO FIXME Extractor Report\n")
    print(f"Files scanned: {result['files_scanned']}\nFindings: {len(result['findings'])}\n")
    for k,v in result["counts"].items():
        if v: print(f"- {k}: {v}")
    for item in result["findings"]:
        print(f"\n## {item['code']} - {item['file']}:{item['line']}\n{item['tag']}: {item['excerpt']}")

def main():
    ap=argparse.ArgumentParser(description="Read-only tech debt comment inventory.")
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--format", choices=["markdown","json"], default="markdown")
    args=ap.parse_args(); result=scan(args.paths)
    print(json.dumps(result, indent=2) if args.format=="json" else "", end="")
    if args.format=="markdown": print_markdown(result)
if __name__=="__main__": main()
