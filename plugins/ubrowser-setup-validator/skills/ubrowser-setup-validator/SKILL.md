---
name: ubrowser-setup-validator
description: Install, validate, or diagnose the upstream uBrowser MCP runtime and its local Playwright dependencies. Use for missing server files, MCP startup failures, tool-surface checks, or a clean uBrowser setup; do not use for ordinary browser automation.
license: MIT
metadata:
  version: 1.0.0
  author: JustHandled Labs
---

# uBrowser Setup Validator

Set up or verify the upstream [Lulzx/ubrowser](https://github.com/Lulzx/ubrowser) runtime without implying that JustHandled Labs created or maintains that project.

## Route the request

- For a read-only diagnosis, inspect the runtime and run the validator without installation flags.
- For installation or repair, read [references/setup.md](references/setup.md) and confirm that the user authorized the download and destination before running an install command.
- Before enabling persistent sessions, authenticated browsing, or work on sensitive sites, read [references/security.md](references/security.md).

## Validate first

Run from this skill directory:

```bash
node scripts/install-and-validate.mjs --runtime <path-to-runtime> --probe --json
```

The validator checks the pinned upstream revision, Node version, package and lock files, compiled server entry point, declared tool surface, optional Chromium availability, and an MCP initialize/tools-list handshake. Treat `READY` as evidence only for the checks actually run.

With authorization to contact one target, add `--smoke-url https://example.com` to verify a real navigation. Use only a harmless HTTPS page the user is authorized to access.

## Install or repair

Installation writes files and downloads dependencies. Use it only when the user has authorized those effects:

```bash
node scripts/install-and-validate.mjs --runtime <empty-destination> --install --accept-downloads --probe --json
```

Add `--install-browser` to download Playwright Chromium and require its executable to be present. Do not overwrite a non-empty destination or silently update an existing runtime.

## Report accurately

- Separate a successful local probe from client configuration and real-site automation.
- Never repeat the upstream `98%` claim as a general guarantee. Describe batching and compact snapshots as design choices whose savings depend on the workflow, model, page, and baseline.
- The runtime exposes 11 MCP tools. Session persistence is behavior, not a `browser_session` tool.
- Do not claim support for a client or operating system that was not tested in the current run.
- Do not treat installation, a successful probe, a marketplace view, or an owner test as buyer demand or revenue.

## Boundaries

- Use only sites and accounts the user is authorized to access.
- Do not bypass access controls, CAPTCHAs, anti-bot controls, rate limits, or site terms.
- Do not collect credentials, private data, or session material for unrelated purposes.
- Keep the upstream runtime and the JustHandled companion visibly distinct.
