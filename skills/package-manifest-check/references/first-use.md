# First use: inspect a difference, not a safety verdict

From the package-manifest-check folder, with Python 3.10+ installed:

```
python scripts/check_package.py examples/matching.zip examples/expected.json --manifest-sha256 a15c1fdef8d8b49cf63f516212ac5fcced81e5f745f80fe1b69d34bb98a63b64
python scripts/check_package.py examples/changed.zip examples/expected.json --manifest-sha256 a15c1fdef8d8b49cf63f516212ac5fcced81e5f745f80fe1b69d34bb98a63b64
```

The first command returns MATCH and exit 0. The second deliberately returns MISMATCH and exit 1: `demo/notes.txt` is missing, `demo/extra.txt` is extra, and `demo/SKILL.md` is modified. A shell may flag that nonzero exit; it is the expected result, not a crash. These ZIPs contain only inert example text. Do not extract them to use this checker.

This included manifest and hash are **training fixtures, not independent trust evidence**. For real use, obtain an expected manifest from an owner-approved known-good release and its hash from a separately trusted release record or verified publisher channel. A hash inside the same untrusted download is not sufficient. Do not copy the incoming ZIP to create its own purported baseline.

Replace the example paths and hash with those real inputs. Preserve the archive's enclosing folder in manifest paths. Keep the original download unchanged. Review JSON lists before deciding what to investigate; do not infer malware from a mismatch or safety from a match.

Packaging dates, entry order and compression can change an archive hash without changing file bytes. This checker helps explain that distinction. It does not verify empty-directory metadata, executable permissions or publisher signatures.
