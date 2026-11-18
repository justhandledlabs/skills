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
    if not Path(path).is_file():
        raise ValueError("input must be a regular file")
    raw=Path(path).read_bytes().decode('utf-8-sig')
    # splitlines() also treats control/Unicode separators inside a value as new
    # assignments, potentially exposing value fragments as apparent key names.
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\x85\u2028\u2029]|\r(?!\n)', raw):
        raise ValueError('unsupported control character or line separator')
    lines=raw.replace('\r\n', '\n').split('\n')
    out=[]; flagged=[]
    for number,line in enumerate(lines,1):
        stripped=line.strip()
        if stripped.startswith("#"):
            continue
        if not stripped:
            out.append(line); continue
        m=re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            raise ValueError(f"unsupported assignment syntax at line {number}; no output produced")
        key,value=m.group(1),m.group(2)
        # Do not copy a continuation line or guess at multiline dotenv dialects.
        quoted=value.lstrip()
        if quoted.startswith('`'):
            raise ValueError('backtick values are unsupported')
        if quoted.startswith(('"', "'")):
            quote=quoted[0]; escaped=False; closed=False
            for char in quoted[1:]:
                if escaped:
                    escaped=False
                elif char == '\\' and quote == '"':
                    escaped=True
                elif char == quote:
                    closed=True; break
            if not closed:
                raise ValueError(f"multiline or unterminated quoted value at line {number}; no output produced")
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


def linked_output_path(path):
    absolute=path.absolute()
    for part in (absolute, *absolute.parents):
        try:
            info=part.lstat()
        except FileNotFoundError:
            continue
        if part.is_symlink() or getattr(info, 'st_reparse_tag', 0) in (0xA0000003, 0xA000000C):
            return True
    return False

def main():
    ap=argparse.ArgumentParser(description="Create a safe .env.example from .env.")
    ap.add_argument("path", nargs="?", default=".env")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--output", default=".env.example")
    args=ap.parse_args()
    try:
        content=render(args.path)
    except (ValueError, UnicodeError, OSError):
        # Never echo input lines, values, paths or decoding fragments to stderr.
        raise SystemExit("Unable to generate example: unsupported input or read failure; no output written.")
    if args.write:
        try:
            out=Path(args.output)
            source=Path(args.path)
            if linked_output_path(out) or out.resolve()==source.resolve() or (out.exists() and out.samefile(source)):
                raise SystemExit("output must be a separate regular destination; input unchanged")
            if out.exists() and not out.is_file():
                raise SystemExit("output must be a regular file destination")
            if out.exists() and out.stat().st_nlink > 1:
                raise SystemExit("output has multiple hard links; choose a separate destination")
            if out.exists() and not args.force:
                raise SystemExit("target exists; pass --force to overwrite")
            with out.open('w' if args.force else 'x', encoding='utf-8', newline='\n') as handle:
                handle.write(content)
        except OSError:
            raise SystemExit("Unable to write example: destination unavailable.")
    else:
        print(content, end="")
if __name__=="__main__": main()
