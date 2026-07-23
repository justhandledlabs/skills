---
name: todo-fixme-extractor
description: List every TODO, FIXME, HACK, XXX, and BUG comment in your code with file and line. Use when the user says "list the TODOs in my repo", "find tech debt comments", or "where are the FIXMEs".
license: MIT
metadata:
  author: JustHandled Labs
  version: 1.0.0
  price: $0
  credits: 0
  triggers:
    - list the TODOs in my repo
    - find tech debt comments
    - where are the FIXMEs
---

# TODO FIXME Extractor

Inventory tech-debt comments across source files. This is a detector and reporting tool, not a fixer or prioritizer.

## Workflow

1. Run scripts/scan_todo_fixme.py with a repo folder or files.
2. Review file, line, tag, and trimmed comment text.
3. Use per-tag counts to scope cleanup work.

## Guardrails

- Read files only.
- Do not edit code or rank work by business priority.
- Ignore dependency and build folders.

## Verification

Run tests/test_todo_fixme.py. Risky fixture must produce findings and clean fixture must produce zero findings.

## Commercial Terms

Price: $0 / 0 credits. Free commercial use for personal or internal team workflows. Do not resell or redistribute the package as-is.
