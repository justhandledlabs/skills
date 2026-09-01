#!/usr/bin/env node

import { access, mkdir, readdir, readFile, stat } from "node:fs/promises";
import { constants as fsConstants, existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import readline from "node:readline";
import { spawn, spawnSync } from "node:child_process";

const UPSTREAM_URL = "https://github.com/Lulzx/ubrowser.git";
const PINNED_COMMIT = "ab354d9d7dd446a10f37a5d9b4ac3f900ec67635";
const EXPECTED_TOOLS = [
  "browser_batch",
  "browser_click",
  "browser_console",
  "browser_inspect",
  "browser_navigate",
  "browser_network",
  "browser_pages",
  "browser_scroll",
  "browser_select",
  "browser_snapshot",
  "browser_type",
];

function usage() {
  return `uBrowser Setup & Compatibility Validator

Usage:
  node scripts/install-and-validate.mjs --runtime <path> [options]

Options:
  --install             Clone the pinned upstream revision, install locked dependencies, and build.
  --install-browser     Also download Playwright Chromium; requires --install.
  --accept-downloads    Confirm authorization for network downloads and destination writes.
  --probe               Start the MCP server and verify initialize plus tools/list.
  --smoke-url <https>   With --probe, navigate to one authorized HTTPS URL.
  --require-browser     Require the Playwright Chromium executable to exist.
  --json                Emit machine-readable JSON.
  --help                Show this help.
`;
}

function parseArgs(argv) {
  const options = {
    runtime: null,
    install: false,
    installBrowser: false,
    acceptDownloads: false,
    probe: false,
    smokeUrl: null,
    requireBrowser: false,
    json: false,
    help: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--runtime") options.runtime = argv[++i];
    else if (arg === "--install") options.install = true;
    else if (arg === "--install-browser") options.installBrowser = true;
    else if (arg === "--accept-downloads") options.acceptDownloads = true;
    else if (arg === "--probe") options.probe = true;
    else if (arg === "--smoke-url") options.smokeUrl = argv[++i];
    else if (arg === "--require-browser") options.requireBrowser = true;
    else if (arg === "--json") options.json = true;
    else if (arg === "--help" || arg === "-h") options.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function commandName(base) {
  return process.platform === "win32" ? `${base}.cmd` : base;
}

function run(command, args, cwd) {
  const needsWindowsCommandShell = process.platform === "win32" && /\.(cmd|bat)$/i.test(command);
  const executable = needsWindowsCommandShell ? (process.env.ComSpec || "cmd.exe") : command;
  const executableArgs = needsWindowsCommandShell
    ? ["/d", "/s", "/c", `${command} ${args.join(" ")}`]
    : args;
  const result = spawnSync(executable, executableArgs, {
    cwd,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    shell: false,
    windowsHide: true,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || "command failed").trim();
    throw new Error(`${command} ${args.join(" ")} failed: ${detail}`);
  }
  return (result.stdout || "").trim();
}

async function isNonEmptyDirectory(target) {
  try {
    const info = await stat(target);
    if (!info.isDirectory()) return true;
    return (await readdir(target)).length > 0;
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
}

async function installRuntime(runtime, installBrowser) {
  if (await isNonEmptyDirectory(runtime)) {
    throw new Error("Installation destination must be absent or empty; existing runtimes are never overwritten.");
  }
  await mkdir(path.dirname(runtime), { recursive: true });
  run("git", ["clone", UPSTREAM_URL, runtime], process.cwd());
  run("git", ["checkout", "--detach", PINNED_COMMIT], runtime);
  run(commandName("npm"), ["ci"], runtime);
  if (installBrowser) run(commandName("npx"), ["playwright", "install", "chromium"], runtime);
  run(commandName("npm"), ["run", "build"], runtime);
}

async function checkFile(file) {
  try {
    await access(file, fsConstants.R_OK);
    return true;
  } catch {
    return false;
  }
}

function addCheck(checks, name, passed, required, evidence) {
  checks.push({ name, passed: Boolean(passed), required: Boolean(required), evidence });
}

async function chromiumExecutable(runtime) {
  const expression = "import('playwright').then(({chromium})=>process.stdout.write(chromium.executablePath())).catch(e=>{process.stderr.write(String(e));process.exit(1)})";
  try {
    const executable = run(process.execPath, ["--input-type=module", "-e", expression], runtime);
    return { path: executable, exists: Boolean(executable && existsSync(executable)) };
  } catch (error) {
    return { path: null, exists: false, error: error.message };
  }
}

function waitForResponse(pending, id, timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`Timed out waiting for MCP response ${id}`));
    }, timeoutMs);
    pending.set(id, (message) => {
      clearTimeout(timer);
      resolve(message);
    });
  });
}

async function probeServer(runtime, smokeUrl) {
  const entry = path.join(runtime, "build", "index.js");
  const child = spawn(process.execPath, [entry], {
    cwd: runtime,
    stdio: ["pipe", "pipe", "pipe"],
    env: { ...process.env, UBROWSER_PROFILE_DIR: path.join(runtime, ".validator-profile") },
  });
  const pending = new Map();
  let stderr = "";
  child.stderr.setEncoding("utf8");
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  const lines = readline.createInterface({ input: child.stdout });
  lines.on("line", (line) => {
    try {
      const message = JSON.parse(line);
      if (message.id !== undefined && pending.has(message.id)) {
        const resolve = pending.get(message.id);
        pending.delete(message.id);
        resolve(message);
      }
    } catch {
      // A usable stdio server will answer the protocol requests below.
    }
  });

  const send = (message) => child.stdin.write(`${JSON.stringify(message)}\n`);
  try {
    const initialized = waitForResponse(pending, 1);
    send({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: {},
        clientInfo: { name: "justhandled-ubrowser-validator", version: "1.0.0" },
      },
    });
    const initializeResponse = await initialized;
    if (initializeResponse.error) throw new Error(JSON.stringify(initializeResponse.error));
    send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
    const toolsListed = waitForResponse(pending, 2);
    send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
    const toolsResponse = await toolsListed;
    if (toolsResponse.error) throw new Error(JSON.stringify(toolsResponse.error));
    const names = (toolsResponse.result?.tools || []).map((tool) => tool.name).sort();
    let navigation = null;
    if (smokeUrl) {
      const navigationResponsePending = waitForResponse(pending, 3, 20000);
      send({
        jsonrpc: "2.0",
        id: 3,
        method: "tools/call",
        params: {
          name: "browser_navigate",
          arguments: {
            url: smokeUrl,
            waitUntil: "domcontentloaded",
            snapshot: { include: true, maxElements: 20 },
            timeout: 15000,
          },
        },
      });
      const navigationResponse = await navigationResponsePending;
      if (navigationResponse.error) throw new Error(JSON.stringify(navigationResponse.error));
      const textContent = navigationResponse.result?.content?.find((item) => item.type === "text")?.text;
      let body = null;
      try { body = textContent ? JSON.parse(textContent) : null; } catch { body = textContent; }
      navigation = {
        passed: navigationResponse.result?.isError !== true && body?.ok !== false,
        url: smokeUrl,
        result: body,
      };
    }
    return {
      passed: JSON.stringify(names) === JSON.stringify(EXPECTED_TOOLS),
      tools: names,
      serverInfo: initializeResponse.result?.serverInfo || null,
      protocolVersion: initializeResponse.result?.protocolVersion || null,
      navigation,
      stderr: stderr.trim(),
    };
  } finally {
    child.stdin.end();
    child.kill("SIGTERM");
    lines.close();
  }
}

async function validate(runtime, options) {
  const checks = [];
  const nodeMajor = Number(process.versions.node.split(".")[0]);
  addCheck(checks, "Node.js version", nodeMajor >= 18, true, process.versions.node);

  const packagePath = path.join(runtime, "package.json");
  const lockPath = path.join(runtime, "package-lock.json");
  const entryPath = path.join(runtime, "build", "index.js");
  addCheck(checks, "package.json", await checkFile(packagePath), true, packagePath);
  addCheck(checks, "package-lock.json", await checkFile(lockPath), true, lockPath);
  addCheck(checks, "compiled MCP entry", await checkFile(entryPath), true, entryPath);

  if (await checkFile(packagePath)) {
    const packageData = JSON.parse(await readFile(packagePath, "utf8"));
    addCheck(
      checks,
      "upstream package identity",
      packageData.name === "ubrowser" && packageData.version === "1.0.1",
      true,
      `${packageData.name || "unknown"}@${packageData.version || "unknown"}`,
    );
  }

  let commit = null;
  try {
    commit = run("git", ["rev-parse", "HEAD"], runtime);
    addCheck(checks, "pinned upstream revision", commit === PINNED_COMMIT, true, commit);
  } catch (error) {
    addCheck(checks, "pinned upstream revision", false, true, error.message);
  }

  const browser = await chromiumExecutable(runtime);
  addCheck(
    checks,
    "Playwright Chromium",
    browser.exists,
    options.requireBrowser,
    browser.exists ? browser.path : (browser.error || browser.path || "not installed"),
  );

  let probe = null;
  if (options.probe && await checkFile(entryPath)) {
    try {
      probe = await probeServer(runtime, options.smokeUrl);
      addCheck(checks, "MCP initialize and tool surface", probe.passed, true, probe.tools.join(", "));
      if (options.smokeUrl) {
        addCheck(
          checks,
          "authorized HTTPS navigation",
          probe.navigation?.passed,
          true,
          probe.navigation?.passed ? options.smokeUrl : JSON.stringify(probe.navigation?.result || null),
        );
      }
    } catch (error) {
      addCheck(checks, "MCP initialize and tool surface", false, true, error.message);
    }
  }

  const requiredFailures = checks.filter((check) => check.required && !check.passed);
  return {
    product: "uBrowser Setup & Compatibility Validator",
    companionVersion: "1.0.0",
    upstream: { url: UPSTREAM_URL, pinnedCommit: PINNED_COMMIT, observedCommit: commit },
    runtime,
    status: requiredFailures.length === 0 ? "READY" : "REVIEW",
    checks,
    probe,
    limitations: [
      "READY covers only the checks performed by this command.",
      options.smokeUrl
        ? `The only real-site navigation performed was ${options.smokeUrl}; no authenticated workflow was tested.`
        : "No real-site navigation or authenticated workflow was performed.",
      "Installation and owner testing are operational evidence, not demand or revenue.",
    ],
  };
}

async function main() {
  let options;
  try {
    options = parseArgs(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`${error.message}\n\n${usage()}`);
    process.exitCode = 2;
    return;
  }
  if (options.help) {
    process.stdout.write(usage());
    return;
  }
  if (!options.runtime) {
    process.stderr.write(`--runtime is required.\n\n${usage()}`);
    process.exitCode = 2;
    return;
  }
  if (options.installBrowser && !options.install) {
    process.stderr.write("--install-browser requires --install.\n");
    process.exitCode = 2;
    return;
  }
  if (options.smokeUrl && !options.probe) {
    process.stderr.write("--smoke-url requires --probe.\n");
    process.exitCode = 2;
    return;
  }
  if (options.smokeUrl) {
    try {
      const smoke = new URL(options.smokeUrl);
      if (smoke.protocol !== "https:") throw new Error("not HTTPS");
    } catch {
      process.stderr.write("--smoke-url must be a valid HTTPS URL.\n");
      process.exitCode = 2;
      return;
    }
  }
  if (options.install && !options.acceptDownloads) {
    process.stderr.write("Installation requires --accept-downloads to confirm network downloads and destination writes.\n");
    process.exitCode = 2;
    return;
  }

  const runtime = path.resolve(options.runtime);
  try {
    if (options.install) await installRuntime(runtime, options.installBrowser);
    const report = await validate(runtime, {
      ...options,
      requireBrowser: options.requireBrowser || options.installBrowser,
    });
    if (options.json) process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
    else {
      process.stdout.write(`${report.status}: ${report.runtime}\n`);
      for (const check of report.checks) {
        const mark = check.passed ? "PASS" : (check.required ? "FAIL" : "NOTE");
        process.stdout.write(`${mark} ${check.name}: ${check.evidence}\n`);
      }
    }
    if (report.status !== "READY") process.exitCode = 2;
  } catch (error) {
    process.stderr.write(`REVIEW: ${error.message}\n`);
    process.exitCode = 2;
  }
}

await main();
