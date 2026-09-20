# Version 1 contract

Manifest UTF-8 JSON (no duplicate keys):

```json
{"schema_version":1,"files":{"skill/SKILL.md":"64 lowercase hexadecimal SHA-256 characters"}}
```

File paths must match ZIP members exactly, including the enclosing package folder. At least one file is required. No globbing, ignored files or automatic root stripping. Empty directories do not count as files. All file types, including dotfiles and executable extensions, are compared as bytes, never run.

Obtain the manifest digest through a separately trusted channel. The program checks that supplied digest but cannot establish how the user obtained it. It records `trust_source_authenticated: false` intentionally. It does not authenticate publisher identity or signatures.

Limits: archive 32 MiB compressed; 1 MiB manifest; 2,000 ZIP entries; 500 files in manifest; 8 MiB per expanded file; 32 MiB expanded total; compression ratio at most 200:1. Encrypted entries, links, special files, duplicate/casefold/Unicode-normalized collisions and unsafe portable paths are refused. Backslashes, traversal, absolute paths, drive paths, reserved Windows names and trailing dot/space are unsupported. Symlink/reparse input paths or ancestors are refused.

The archive is read into bounded memory from a regular file. Before/after metadata checks detect some changes, not adversarial races. Use stable local snapshots; this is not a sandbox. ZIP metadata never gets materialized on disk. Permissions and executable modes are not certified.

Exit codes: 0 MATCH, 1 MISMATCH, 2 CANNOT_ASSESS. JSON on stdout. No output-file option to avoid overwriting evidence. Use the caller's explicit choice if saving a report. Local error reports use fixed reason codes, not OS error strings or absolute paths.

