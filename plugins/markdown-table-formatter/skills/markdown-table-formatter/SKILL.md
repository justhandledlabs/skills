---
name: markdown-table-formatter
description: Align messy Markdown tables and normalize their columns, or build a table from CSV. Use when the user says "fix my markdown table", "align this table", or "csv to markdown table".
metadata:
  author: JustHandled Labs
  version: 1.0.0
  price: $0
  credits: 0
  triggers:
    - fix my markdown table
    - align this table
    - csv to markdown table
---

# Markdown Table Formatter

Format GitHub-Flavored Markdown tables and convert simple CSV or TSV input into a Markdown table. This formatter changes spacing and alignment, not cell content.

## Workflow

1. Run scripts/format_markdown_table.py with a Markdown file or stdin.
2. Use --from-csv for CSV or TSV input.
3. Review stdout.
4. Write in place only with --write and --force.

## Guardrails

- Do not change cell content.
- Do not overwrite files without --force.
- Do not fetch remote input.

## Verification

Run tests/test_markdown_table.py. Formatted output must match fixtures/expected/clean.md.

## Commercial Terms

Price: $0 / 0 credits. Free commercial use for personal or internal team workflows. Do not resell or redistribute the package as-is.
