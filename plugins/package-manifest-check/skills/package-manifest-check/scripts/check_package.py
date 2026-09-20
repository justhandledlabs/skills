"""Offline ZIP file-manifest comparison. No extraction, subprocesses or network."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import unicodedata
import zipfile
import zlib

ARCHIVE_MAX = 32 * 1024 * 1024
MANIFEST_MAX = 1024 * 1024
FILE_MAX = 8 * 1024 * 1024
HEX = re.compile(r'[0-9a-f]{64}\Z')
RESERVED = re.compile(r'(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?\Z', re.I)

class Refusal(Exception):
    pass

def sha(data):
    return hashlib.sha256(data).hexdigest()

def identity(s):
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns

def read_local(value, limit):
    p = Path(os.path.abspath(value))
    for part in [p, *p.parents]:
        s = part.lstat()
        if stat.S_ISLNK(s.st_mode) or getattr(s, 'st_file_attributes', 0) & 0x400:
            raise Refusal('linked_input')
    before = p.stat()
    if not stat.S_ISREG(before.st_mode):
        raise Refusal('nonregular_input')
    if before.st_size > limit:
        raise Refusal('input_size_limit')
    with p.open('rb') as f:
        if identity(os.fstat(f.fileno())) != identity(before):
            raise Refusal('input_changed')
        data = f.read(limit + 1)
        if identity(os.fstat(f.fileno())) != identity(before):
            raise Refusal('input_changed')
    if len(data) > limit or identity(p.stat()) != identity(before):
        raise Refusal('input_changed')
    return data

def safe_name(name):
    if not isinstance(name, str) or not name or len(name) > 240:
        raise Refusal('unsafe_path')
    if any(ord(c) < 32 or ord(c) == 127 or c in '\\:<>"|?*' for c in name):
        raise Refusal('unsafe_path')
    parts = name.split('/')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) or RESERVED.fullmatch(p) for p in parts):
        raise Refusal('unsafe_path')
    return unicodedata.normalize('NFC', name).casefold()

def unique_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise Refusal('duplicate_manifest_key')
        result[k] = v
    return result

def validate_path_tree(paths, files):
    """Check implicit directories too; aliases must not depend on extraction OS."""
    spelling = {}
    file_keys = {safe_name(name) for name in files}
    for name in paths:
        parts = name.split('/')
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            key = safe_name(prefix)
            if key in spelling and spelling[key] != prefix:
                raise Refusal('path_collision')
            spelling[key] = prefix
            if i < len(parts) and key in file_keys:
                raise Refusal('path_collision')

def parse_manifest(raw):
    d = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_pairs)
    if not isinstance(d, dict) or set(d) != {'schema_version', 'files'} or type(d['schema_version']) is not int or d['schema_version'] != 1:
        raise Refusal('unsupported_manifest')
    files = d['files']
    if not isinstance(files, dict) or not 1 <= len(files) <= 500:
        raise Refusal('manifest_file_count')
    seen = set()
    for name, digest in files.items():
        key = safe_name(name)
        if key in seen:
            raise Refusal('path_collision')
        seen.add(key)
        if not isinstance(digest, str) or not HEX.fullmatch(digest):
            raise Refusal('invalid_file_digest')
    validate_path_tree(files, files)
    return files

def archive_files(raw):
    result, names, paths, total = {}, set(), [], 0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if not 1 <= len(entries) <= 2000:
            raise Refusal('archive_entry_limit')
        for entry in entries:
            # ZipInfo truncates filenames at NUL; reject original spelling too.
            if entry.orig_filename != entry.filename:
                raise Refusal('unsafe_path')
            name = entry.filename[:-1] if entry.is_dir() else entry.filename
            key = safe_name(name)
            if key in names:
                raise Refusal('path_collision')
            names.add(key)
            paths.append(name)
            mode = entry.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if kind not in (0, stat.S_IFDIR if entry.is_dir() else stat.S_IFREG):
                raise Refusal('linked_or_special_entry')
            if entry.flag_bits & 1:
                raise Refusal('encrypted_entry')
            if entry.is_dir():
                if entry.file_size:
                    raise Refusal('directory_payload')
                continue
            if entry.file_size > FILE_MAX or entry.file_size > 200 * max(1, entry.compress_size):
                raise Refusal('expanded_size_limit')
            total += entry.file_size
            if total > ARCHIVE_MAX:
                raise Refusal('expanded_size_limit')
            with z.open(entry) as f:
                contents = f.read(FILE_MAX + 1)
            if len(contents) != entry.file_size or len(contents) > FILE_MAX:
                raise Refusal('invalid_entry_size')
            result[entry.filename] = sha(contents)
    validate_path_tree(paths, result)
    return result

def compare(package, manifest, manifest_sha256):
    report = {'schema_version': 1, 'status': 'CANNOT_ASSESS',
              'scope': 'ZIP file bytes only; not Git revision, permissions or safety',
              'trust_source_authenticated': False, 'content_safety': 'NOT_ASSESSED'}
    try:
        if not isinstance(manifest_sha256, str) or not HEX.fullmatch(manifest_sha256):
            raise Refusal('trusted_manifest_digest_required')
        raw_manifest = read_local(manifest, MANIFEST_MAX)
        if sha(raw_manifest) != manifest_sha256:
            raise Refusal('manifest_digest_mismatch')
        expected = parse_manifest(raw_manifest)
        raw = read_local(package, ARCHIVE_MAX)
        actual = archive_files(raw)
        report.update(manifest_sha256=sha(raw_manifest), archive_sha256=sha(raw),
                      missing=sorted(set(expected)-set(actual)),
                      extra=sorted(set(actual)-set(expected)),
                      modified=sorted(k for k in set(actual)&set(expected) if actual[k] != expected[k]),
                      checked_files=len(actual))
        report['status'] = 'MISMATCH' if any(report[k] for k in ('missing','extra','modified')) else 'MATCH'
    except Refusal as e:
        report['reason'] = str(e)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error):
        report['reason'] = 'unreadable_or_invalid_input'
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package'); p.add_argument('manifest'); p.add_argument('--manifest-sha256', required=True)
    a = p.parse_args(); report = compare(a.package, a.manifest, a.manifest_sha256)
    print(json.dumps(report, sort_keys=True, indent=2))
    return {'MATCH':0, 'MISMATCH':1, 'CANNOT_ASSESS':2}[report['status']]

if __name__ == '__main__':
    raise SystemExit(main())
