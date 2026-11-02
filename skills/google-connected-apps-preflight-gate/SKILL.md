---
name: google-connected-apps-preflight-gate
description: Audit an MCP server and Connected Apps listing for Google's preview submission requirements. Use before entering an app in Connected Console, when diagnosing a rejected or incomplete setup, or when checking endpoint transport, domain verification, OAuth discovery, tool annotations and schemas, listing metadata, legal links, and category capability coverage. This is a read-only pre-flight, not a submission or approval guarantee.
---

# Google Connected Apps Pre-flight Gate

Produce a source-linked PASS, FAIL, or CAN'T VERIFY result for each current Google Connected Apps pre-submit check. Never register, submit, approve, authenticate to, or change the user's server or listing.

## Workflow

1. Read [references/input-contract.md](references/input-contract.md) and collect one JSON packet. Never place OAuth secrets, bearer tokens, cookies, or private test credentials in it.
2. Read [references/google-rules.md](references/google-rules.md) when a rule, auth model, or category baseline is disputed. Treat Google's current docs and Connected Console as authoritative.
3. For public live checks, run:

```bash
python scripts/google_connected_apps_preflight.py app.json --live --json-output report.json --markdown-output report.md
```

4. If authentication blocks `tools/list`, export or paste a sanitized `tools_snapshot` from MCP Inspector or Google Developer Mode and rerun. Do not request an access token.
5. Return the headline exactly as `Ready`, `Fix N items`, or `Verify N items`. Preserve every finding's status, exact fix, evidence, and source link.
6. Give the user the generated Connected Console checklist. Order endpoint and verification blockers before OAuth, tools, and listing polish.

## Result rules

- `PASS` means the supplied or publicly observable evidence satisfies the automated check.
- `FAIL` means the evidence contradicts a documented requirement and includes a specific fix.
- `CAN'T VERIFY` means the evidence is absent, access-controlled, or requires a current Connected Console value. Do not turn uncertainty into a pass or fail.
- An optional GET returning HTTP 405 is allowed. Fail the transport check only when the required JSON-RPC POST route returns 405 or otherwise rejects Streamable HTTP.
- OAuth 2.1 with PKCE S256 is the preferred user-delegated model. PKCE is mandatory when the app claims OAuth 2.1, but Google also documents OAuth 2.0 and machine-to-machine paths. Apply the rule to the declared auth model instead of failing every non-OAuth app.
- Do not hardcode category recommendations as mandatory capabilities. Compare against the exact baseline copied from the current Connected Console category.
- A `Ready` result is not a guarantee of Google approval, ranking, traffic, installations, or sales.

## Safety and permissions

- Use only public unauthenticated GET and JSON-RPC POST requests to the user-supplied MCP endpoint, declared OAuth metadata URLs, well-known token URL, and supplied legal URLs.
- Read the local JSON packet and icon. Write only report paths chosen by the user.
- Never follow a redirect when checking `/.well-known/google-connected-apps`.
- Never send credentials, mutate server state, call business tools, register an app, or submit to Connected Console.
- Re-check the linked Google docs before a consequential submission because Connected Apps is in preview.

