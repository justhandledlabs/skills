---
name: env-example-generator
description: Turn a .env into a shareable .env.example with keys preserved and values stripped. Use when the user says "make an env example", "redact my .env", or "create .env.example".
metadata:
  author: JustHandled Labs
  version: 1.0.0
  price: $0
  credits: 0
  triggers:
    - make an env example
    - redact my .env
    - create .env.example
---

# Env Example Generator

Transform a .env file into safe .env.example content. This transformer preserves keys, comments, blank lines, and order, but never prints original values.

## Workflow

1. Run scripts/generate_env_example.py with a .env path, defaulting to ./.env.
2. Review stdout. It contains .env.example content and a secret-looking key summary.
3. Write .env.example only with --write. Existing files require --force.

## Guardrails

- Do not print or copy original values.
- Do not read .env.example as input.
- Do not validate application runtime behavior.

## Verification

Run tests/test_env_example.py. Output must match fixtures/expected/.env.example and must not include input values.

## Commercial Terms

Price: $0 / 0 credits. Free commercial use for personal or internal team workflows. Do not resell or redistribute the package as-is.
