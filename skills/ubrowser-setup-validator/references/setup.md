# Setup and repair

## Requirements

- Git available on the command line.
- Node.js 18 or newer.
- Network access to GitHub and the npm registry for installation.
- Additional network access to Playwright's browser download host when Chromium is requested.
- Write permission to an empty destination chosen by the user.

## Read-only validation

Use this when a uBrowser checkout already exists:

```bash
node scripts/install-and-validate.mjs --runtime <existing-path> --probe --json
```

Add `--require-browser` to fail unless the locally installed Playwright package points to an existing Chromium executable.

With permission to contact one harmless target, add `--smoke-url https://example.com` to verify that Chromium can navigate and return a compact snapshot.

## Clean installation

The installer refuses a non-empty destination. It clones the official repository, checks out the pinned revision, installs exact locked dependencies, and builds the server:

```bash
node scripts/install-and-validate.mjs --runtime <empty-path> --install --accept-downloads --probe --json
```

To download Chromium as part of the same authorized operation:

```bash
node scripts/install-and-validate.mjs --runtime <empty-path> --install --install-browser --accept-downloads --probe --json
```

## MCP configuration

Configure a local stdio MCP server with:

- command: `node`
- first argument: the absolute path to `<runtime>/build/index.js`
- working directory: the runtime directory, when the client supports one

The upstream README documents this Claude Code command after installation:

```bash
claude mcp add ubrowser -- node "/absolute/path/to/ubrowser/build/index.js"
```

For other clients, translate the same command and argument into that client's local MCP configuration. Do not claim compatibility until the client can initialize the server and list its tools.

## Expected tool surface

The pinned revision exposes:

- `browser_batch`
- `browser_navigate`
- `browser_click`
- `browser_type`
- `browser_select`
- `browser_scroll`
- `browser_snapshot`
- `browser_pages`
- `browser_inspect`
- `browser_console`
- `browser_network`

There is no `browser_session` tool. Persistence is implemented through the browser profile directory.

## Updating

Do not silently pull the latest upstream revision. Evaluate a newer revision separately, rerun the protocol and browser smoke tests, compare tool schemas and security-relevant defaults, and update the pinned revision only in a new companion release.
