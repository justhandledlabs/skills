# Supported Options

Input: .env or *.env files, excluding .env.example.

Output: .env.example content printed to stdout by default. Use --write to create a file. Use --force to overwrite.

Source comments and assignment values are omitted. Generated review summaries list key names only; key names can themselves be sensitive. This is not a general secret detector. Only single-line assignments with LF or CRLF line endings are supported; a leading UTF-8 BOM is accepted. Backtick values and nonstandard line separators are rejected. Multiline, malformed or unreadable input stops before output.

Output aliases of the input, multiply hard-linked output files, and output paths traversing symbolic links or junctions are rejected. A symlink input resolving to a regular file is allowed. Concurrent filesystem manipulation is outside the guarantee. Relative output paths resolve from the current working directory, not the input's folder; prefer an explicit absolute path.
