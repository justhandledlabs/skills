# Google Connected Apps rule matrix

Rules were reviewed on 2026-10-30. Google Connected Apps is in preview, so re-check the linked pages before submission.

| ID | Automated check | Current interpretation | Source |
|---|---|---|---|
| GCA-01 | Public HTTPS Streamable HTTP | Test JSON-RPC POST `initialize`. A POST 405 matches Google's legacy SSE-only troubleshooting case. An optional GET may validly return 405. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites), [Troubleshooting](https://developers.google.com/connected-apps/gpc/troubleshooting), [MCP server optimization](https://developers.google.com/connected-apps/mcp/server-optimization) |
| GCA-02 | One global endpoint | A global launch uses one endpoint. Separate region-specific addresses are unsupported; a region-only launch can use its single regional endpoint. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites) |
| GCA-03 | Domain token | `/.well-known/google-connected-apps` must return the current token with HTTP 200 and no redirect. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites) |
| GCA-04 | OAuth and PKCE | Google highly recommends OAuth 2.1. PKCE is mandatory for OAuth 2.1 and optional for OAuth 2.0. S256 should be advertised for an OAuth 2.1 authorization-code app. PKCE is not applicable to no-auth or client-credentials flows. | [OAuth guide](https://developers.google.com/connected-apps/mcp/oauth) |
| GCA-05 | Discovery metadata | Authorization-code discovery needs authorization and token endpoints plus `code` response support. Dynamic registration also needs a registration endpoint; manual registration uses a configured client ID and secret instead. | [OAuth guide](https://developers.google.com/connected-apps/mcp/oauth) |
| GCA-06 | Tool hints | Each tool should carry explicit `readOnlyHint` or `destructiveHint` annotations that match behavior. | [MCP server optimization](https://developers.google.com/connected-apps/mcp/server-optimization) |
| GCA-07 | Schemas and names | Use strongly typed schemas, semantic descriptions, and clear verb-noun names. This package performs structural checks, not complete JSON Schema proof. | [MCP development](https://developers.google.com/connected-apps/mcp), [MCP server optimization](https://developers.google.com/connected-apps/mcp/server-optimization) |
| GCA-08 | Description | Listing description must be fewer than 30 words. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites) |
| GCA-09 | Capabilities and prompts | Supply at least three capabilities and three prompts. Start at least two prompts with @ followed by the app name; mention the name naturally later in another. Review wording, numbering and quotation marks manually. | [Console submission instructions](https://developers.google.com/connected-apps/gpc/perform-the-steps) |
| GCA-10 | Icon | PNG or JPEG, exactly 512 by 512 pixels, no larger than 1,024 KB. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites) |
| GCA-11 | Legal links | Terms of Service and Privacy Policy URLs must be public and load. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites) |
| GCA-12 | Category coverage | Category is immutable and carries baseline capabilities. Copy the exact current baseline from Connected Console. Public journey recommendations are not treated as a complete mandatory table. | [Prerequisites](https://developers.google.com/connected-apps/gpc/prerequisites), [Register, test, and publish](https://developers.google.com/connected-apps/gpc/perform-the-steps) |

Developer Mode is useful for live debugging and evaluation, but it is not a substitute for this pre-submit listing and evidence checklist: [Developer Mode](https://developers.google.com/connected-apps/mcp/dev-mode).

