---
name: package-manifest-check
description: Compare a downloaded ZIP with a separately trusted SHA-256 file manifest before installation or update. Identify missing, added and changed files without extracting or executing the package.
---

# Package Manifest Check

Version: 1.0.0. Requires Python 3.10+; standard library only.

Read [the input contract](references/contract.md). Obtain the expected file manifest and its SHA-256 from a separately trusted release record. Do not generate the expected inventory from the incoming download and call that verification. If no trusted baseline is available, report that verification cannot be completed.

Run from this skill's folder:

```
python scripts/check_package.py RECEIVED.zip EXPECTED.json --manifest-sha256 TRUSTED_MANIFEST_SHA256
```

Use quoted paths when needed. See [the runnable first-use example](references/first-use.md).

- MATCH: file bytes agree with the supplied manifest. This does not establish publisher identity or safety.
- MISMATCH: inspect the missing, extra and modified lists. Legitimate updates can differ; do not automatically delete, repair or install anything.
- CANNOT_ASSESS: inputs are unavailable, invalid or unsupported. Do not report a completed verification.

The checker prints JSON and does not write files, fetch anything, extract the target or run its code. Filenames in reports may be sensitive; review before sharing. ZIP only: no Git verification, signatures, malware verdict, permissions certification or host patch assessment. A normal archive SHA-256 check is sufficient when only byte-identical delivery needs verification.

Licence: MIT; see LICENSE.md.
