---
name: env-example-generator
description: Turn a .env into a shareable .env.example with keys preserved and values stripped. Use when the user says "make an env example", "redact my .env", or "create .env.example".
license: MIT
metadata:
  author: JustHandled Labs
  version: 1.0.1
  price: $0
  credits: "0"
  triggers: "make an env example; redact my .env; create .env.example"
---

# Env Example Generator

Create a key-only example from supported single-line dotenv assignments. Preserve key order and blank lines; omit source comments and all assignment values. Multiline, malformed or unreadable input stops without output. This is not a general secret detector: key names themselves remain visible and require review before sharing.

MIT distribution version 1.0.1. This distribution retains its existing MIT licence; Agensi's separate buyer terms are unchanged.

## Workflow

1. Run scripts/generate_env_example.py with a .env path, defaulting to ./.env.
2. Review stdout. It contains .env.example content and a secret-looking key summary.
3. Write .env.example only with --write. Existing files require --force.
4. Never use the input file, its link, or a symlink destination as output. Use --force only when the user approved replacing that specific example file. Do not claim protection against concurrent filesystem manipulation.
5. Use regular files only. Output paths must not traverse symlinks/junctions or have multiple hard links. Relative outputs use the current working directory, not the input directory. Read `references/supported-options.md` for supported names and syntax.

## Guardrails

- Do not print or copy original values.
- Do not read .env.example as input.
- Do not validate application runtime behavior.
- Source comments are omitted by default with no preserve-comments option. A generated review summary lists key names only, not source comments or values.
- Do not silently flatten multiline values or echo rejected source lines. Ask for a supported single-line input without requesting secret values in chat.

## Verification

Run `python -m unittest discover tests -v`. Synthetic markers must not appear in stdout, stderr or generated files; rejected inputs must leave existing files unchanged.

## Licence

This GitHub-distributed package is licensed under the MIT License in LICENSE.md. Preserve its copyright and permission notice as required by that licence.
