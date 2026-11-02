# Google Connected Apps Pre-flight Gate

**Result: Ready**

Pass: 12 | Fail: 0 | Can't verify: 0

Rules reviewed: 2026-10-30. Google Connected Apps is in preview. Re-check the linked Google documentation before submission.

## Blocking order

### PASS | GCA-01 | Public HTTPS Streamable HTTP endpoint

POST initialize returned HTTP 200 with a parseable MCP response.

**Exact fix:** No fix indicated. Confirm behavior again in Google Developer Mode.

**Source:** https://developers.google.com/connected-apps/mcp/dev-mode

### PASS | GCA-02 | One global endpoint

Exactly one production endpoint is declared: https://demo-records.example/mcp.

**Exact fix:** No fix indicated.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

### PASS | GCA-03 | Domain verification token

The exact supplied token is present at the required well-known URL with HTTP 200 and no redirect.

**Exact fix:** No fix indicated.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

### PASS | GCA-04 | OAuth 2.1 and PKCE S256

The app is explicitly declared unauthenticated, so OAuth and PKCE are not applicable.

**Exact fix:** No OAuth fix indicated. Confirm the server exposes only data and actions suitable for unauthenticated access.

**Source:** https://developers.google.com/connected-apps/mcp/oauth

### PASS | GCA-05 | OAuth discovery metadata

The app is explicitly declared unauthenticated, so OAuth discovery documents are not applicable.

**Exact fix:** No OAuth metadata fix indicated.

**Source:** https://developers.google.com/connected-apps/mcp/oauth

### PASS | GCA-06 | Explicit tool safety hints

All 1 tools expose an explicit readOnlyHint or destructiveHint in supplied tools_snapshot.

**Exact fix:** No annotation fix indicated. Validate actual behavior in Developer Mode.

**Source:** https://developers.google.com/connected-apps/mcp/server-optimization

### PASS | GCA-07 | Tool schemas, names, and descriptions

All 1 tools passed structural schema and metadata checks in supplied tools_snapshot.

**Exact fix:** No automated fix indicated. This is a structural pre-flight, not full JSON Schema conformance proof.

**Source:** https://developers.google.com/connected-apps/mcp/server-optimization

### PASS | GCA-08 | Listing description under 30 words

Description contains 10 words.

**Exact fix:** No fix indicated.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

### PASS | GCA-09 | Capabilities and example prompts

Listing includes 3 capabilities and 3 prompts; 2 start with the app name.

**Exact fix:** No fix indicated.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

### PASS | GCA-10 | 512px icon under 1MB

PNG icon is 512 by 512 and 2986 bytes.

**Exact fix:** No fix indicated.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

### PASS | GCA-11 | Terms and Privacy links load

Terms of Service HTTP 200; Privacy Policy HTTP 200.

**Exact fix:** No fix indicated.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

### PASS | GCA-12 | Category capability coverage

All 1 supplied baseline capabilities for 'Productivity' are present.

**Exact fix:** No fix indicated. Reconfirm the immutable category and its baseline in Connected Console before submission.

**Source:** https://developers.google.com/connected-apps/gpc/prerequisites

## Connected Console copy-paste checklist

- [x] GCA-01 Public HTTPS Streamable HTTP endpoint: PASS
- [x] GCA-02 One global endpoint: PASS
- [x] GCA-03 Domain verification token: PASS
- [x] GCA-04 OAuth 2.1 and PKCE S256: PASS
- [x] GCA-05 OAuth discovery metadata: PASS
- [x] GCA-06 Explicit tool safety hints: PASS
- [x] GCA-07 Tool schemas, names, and descriptions: PASS
- [x] GCA-08 Listing description under 30 words: PASS
- [x] GCA-09 Capabilities and example prompts: PASS
- [x] GCA-10 512px icon under 1MB: PASS
- [x] GCA-11 Terms and Privacy links load: PASS
- [x] GCA-12 Category capability coverage: PASS

## Limits

- This read-only pre-flight does not submit, register, approve, or change an MCP server or listing.
- A Ready result does not guarantee Google review approval, ranking, traffic, usage, or sales.
- Live tests are unauthenticated. Supply a sanitized tools_snapshot when authentication prevents tool inspection.
- Schema checks are structural and do not prove complete JSON Schema semantics or tool behavior.

Evidence receipt: `11B69D4C68FACD25AA6B5811A7A5E664FE2D57838D7C602BB896DE5F0398379B`
