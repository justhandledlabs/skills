#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import io
import re
import sys
from pathlib import Path

def split_row(line):
    stripped=line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]

def is_separator(cells):
    return bool(cells) and all(re.match(r"^:?-{3,}:?$", c.replace(" ","")) for c in cells)

def alignment(cell):
    c=cell.replace(" ","")
    return (c.startswith(":"), c.endswith(":"))

def sep_for(width, align):
    left,right=align; body="-"*max(3,width)
    if left and right: return ":"+body[1:-1]+":" if len(body)>2 else ":-:"
    if left: return ":"+body[1:]
    if right: return body[:-1]+":"
    return body

def render_table(rows):
    if len(rows)<2 or not is_separator(rows[1]): return None
    cols=max(len(r) for r in rows)
    rows=[r+[""]*(cols-len(r)) for r in rows]
    aligns=[alignment(c) for c in rows[1]]
    widths=[max(len(rows[r][c]) for r in range(len(rows)) if r!=1) for c in range(cols)]
    out=[]
    for idx,row in enumerate(rows):
        vals=[]
        for c,cell in enumerate(row):
            if idx==1: vals.append(sep_for(widths[c], aligns[c]))
            elif aligns[c][1] and not aligns[c][0]: vals.append(cell.rjust(widths[c]))
            else: vals.append(cell.ljust(widths[c]))
        out.append("| " + " | ".join(vals) + " |")
    return out

def format_markdown(text):
    lines=text.splitlines(); out=[]; i=0
    while i<len(lines):
        row=split_row(lines[i])
        if row is None:
            out.append(lines[i]); i+=1; continue
        block=[]; j=i
        while j<len(lines) and split_row(lines[j]) is not None:
            block.append(split_row(lines[j])); j+=1
        rendered=render_table(block)
        if rendered: out.extend(rendered)
        else: out.extend(lines[i:j])
        i=j
    return "\n".join(out).rstrip()+"\n"

def csv_to_table(text):
    dialect=csv.Sniffer().sniff(text, delimiters=",\t")
    rows=list(csv.reader(io.StringIO(text), dialect))
    if len(rows)<2: return ""
    sep=["---" for _ in rows[0]]
    return format_markdown("\n".join("| " + " | ".join(r) + " |" for r in [rows[0], sep] + rows[1:]))

def main():
    ap=argparse.ArgumentParser(description="Format Markdown tables or convert CSV to Markdown.")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--from-csv", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    args=ap.parse_args()
    text=Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    result=csv_to_table(text) if args.from_csv else format_markdown(text)
    if args.write:
        if not args.path: raise SystemExit("--write requires a file path")
        if not args.force: raise SystemExit("pass --force to write in place")
        Path(args.path).write_text(result, encoding="utf-8", newline="\n")
    else:
        print(result, end="")
if __name__=="__main__": main()
