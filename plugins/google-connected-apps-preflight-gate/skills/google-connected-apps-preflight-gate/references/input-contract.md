# Input contract

Save one UTF-8 JSON object. Do not include credentials, tokens, cookies, client secrets, or private test-account data.

```json
{
  "app_name": "Example App",
  "endpoint": "https://mcp.example.com/mcp",
  "declared_endpoints": ["https://mcp.example.com/mcp"],
  "expected_verification_token": "token copied from Connected Console",
  "auth": {
    "mode": "oauth2.1",
    "issuer": "https://auth.example.com",
    "authorization_server_metadata_url": "https://auth.example.com/.well-known/oauth-authorization-server",
    "client_registration": "dynamic"
  },
  "listing": {
    "description": "Example App finds approved project records and prepares cited summaries.",
    "capabilities": ["Find project records", "Summarize approved records", "Cite source records"],
    "example_prompts": [
      "@Example App, find the latest approved project brief.",
      "@Example App, summarize the approved decisions for this project.",
      "Use Example App to cite the source records for this summary."
    ],
    "icon": "icon.png",
    "terms_url": "https://example.com/terms",
    "privacy_url": "https://example.com/privacy",
    "category": "Category selected in Connected Console",
    "category_required_capabilities": ["Find project records"]
  },
  "tools_snapshot": {
    "tools": [
      {
        "name": "find_project_records",
        "description": "Find approved project records matching a supplied query.",
        "inputSchema": {
          "type": "object",
          "properties": {"query": {"type": "string"}},
          "required": ["query"]
        },
        "annotations": {"readOnlyHint": true, "destructiveHint": false}
      }
    ]
  }
}
```

## Authentication modes

- `none`: no sign-in; OAuth checks are not applicable.
- `client-credentials`: machine-to-machine configuration; do not place the client secret in this file.
- `oauth2.1`: user-delegated OAuth 2.1; S256 is required.
- `oauth2.0`: declared OAuth 2.0; the report notes Google's OAuth 2.1 recommendation without inventing a universal failure.
- `user-delegated`: the version is not established; expect CAN'T VERIFY until metadata establishes it.
- `unknown`: no supported auth model has been confirmed.

## Evidence handling

- `expected_verification_token` is optional but required to verify the exact current token. Without it, a valid public token document receives CAN'T VERIFY rather than PASS.
- `declared_endpoints` must list every production address. The auditor cannot infer hidden regional routing from one URL.
- `tools_snapshot` can be copied from an authenticated MCP Inspector or Developer Mode session after removing sensitive values. It lets the auditor inspect metadata without accepting credentials.
- `category_required_capabilities` must be copied from the current Connected Console category. Do not substitute a blog post or a recommended-journeys page.

