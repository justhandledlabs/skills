#!/usr/bin/env python3
"""Read-only Google Connected Apps pre-flight audit.

Uses only the Python standard library. It never registers, submits, mutates, or
authenticates to an MCP server. Live mode sends only GET, HEAD, and JSON-RPC
POST requests needed to inspect public readiness surfaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DOCS = {
    "endpoint": "https://developers.google.com/connected-apps/gpc/prerequisites",
    "mcp": "https://developers.google.com/connected-apps/mcp",
    "oauth": "https://developers.google.com/connected-apps/mcp/oauth",
    "tools": "https://developers.google.com/connected-apps/mcp/server-optimization",
    "troubleshooting": "https://developers.google.com/connected-apps/gpc/troubleshooting",
    "dev_mode": "https://developers.google.com/connected-apps/mcp/dev-mode",
}
DOC_REVIEWED = "2026-10-30"
USER_AGENT = "JustHandledLabs-GoogleConnectedAppsPreflight/1.0"


@dataclass
class Finding:
    id: str
    title: str
    status: str
    priority: int
    evidence: str
    fix: str
    source: str


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class HttpClient:
    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        context = ssl.create_default_context()
        self.opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
        self.no_redirect_opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=context), NoRedirect()
        )

    def request(
        self,
        url: str,
        method: str = "GET",
        data: Optional[bytes] = None,
        headers: Optional[dict[str, str]] = None,
        follow_redirects: bool = True,
    ) -> dict[str, Any]:
        request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
        req = urllib.request.Request(url, data=data, method=method, headers=request_headers)
        opener = self.opener if follow_redirects else self.no_redirect_opener
        try:
            with opener.open(req, timeout=self.timeout) as response:
                body = response.read(2_000_000)
                return {
                    "status": response.status,
                    "url": response.geturl(),
                    "headers": dict(response.headers.items()),
                    "body": body,
                    "error": None,
                }
        except urllib.error.HTTPError as exc:
            body = exc.read(2_000_000) if exc.fp else b""
            return {
                "status": exc.code,
                "url": exc.geturl(),
                "headers": dict(exc.headers.items()) if exc.headers else {},
                "body": body,
                "error": str(exc),
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {"status": None, "url": url, "headers": {}, "body": b"", "error": str(exc)}

    def json_post(self, url: str, payload: dict[str, Any], extra_headers: Optional[dict[str, str]] = None):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-03-26",
            **(extra_headers or {}),
        }
        return self.request(url, "POST", json.dumps(payload).encode("utf-8"), headers)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid UTF-8 JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Input root must be a JSON object")
    return value


def clean_url(value: Any, *, https_only: bool = False) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = urllib.parse.urlparse(value.strip())
    except ValueError:
        return None
    schemes = {"https"} if https_only else {"http", "https"}
    if parsed.scheme not in schemes or not parsed.hostname or parsed.username or parsed.password:
        return None
    return value.strip()


def origin_for(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}"


def decode_jsonish(body: bytes) -> Any:
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in text.splitlines():
            if line.startswith("data:"):
                candidate = line[5:].strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
    return None


def finding(rule_id, title, status, priority, evidence, fix, source):
    return Finding(rule_id, title, status, priority, evidence, fix, source)


def get_nested(data: dict[str, Any], *keys: str, default=None):
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def check_endpoint(data, live, client, observations):
    endpoint = clean_url(data.get("endpoint"), https_only=True)
    if not endpoint:
        return finding(
            "GCA-01", "Public HTTPS Streamable HTTP endpoint", "FAIL", 10,
            "No valid public HTTPS endpoint was supplied.",
            "Provide the exact public HTTPS MCP endpoint used for JSON-RPC POST requests.", DOCS["endpoint"]
        ), None, None
    if not live:
        return finding(
            "GCA-01", "Public HTTPS Streamable HTTP endpoint", "CAN'T VERIFY", 10,
            f"Endpoint is syntactically valid ({endpoint}), but live transport testing was not requested.",
            "Run again with --live. The gate tests POST initialize; an optional GET returning 405 is not a failure.", DOCS["troubleshooting"]
        ), endpoint, None

    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "jh-connected-apps-preflight", "version": "1.0.1"},
        },
    }
    response = client.json_post(endpoint, payload)
    observations["initialize"] = public_observation(response)
    status = response["status"]
    if status == 405:
        return finding(
            "GCA-01", "Public HTTPS Streamable HTTP endpoint", "FAIL", 10,
            "POST initialize returned HTTP 405, which matches Google's legacy SSE-only failure case.",
            "Expose one Streamable HTTP endpoint that accepts JSON-RPC POST initialize, tools/list, and tools/call.", DOCS["troubleshooting"]
        ), endpoint, response
    if status in (401, 403):
        return finding(
            "GCA-01", "Public HTTPS Streamable HTTP endpoint", "PASS", 10,
            f"The public HTTPS endpoint accepted the POST route and returned HTTP {status}, indicating authentication is required rather than an SSE-only route.",
            "No transport fix indicated. Complete the OAuth checks and test authenticated execution in Developer Mode.", DOCS["mcp"]
        ), endpoint, response
    if status is not None and 200 <= status < 300:
        parsed = decode_jsonish(response["body"])
        if parsed is None:
            return finding(
                "GCA-01", "Public HTTPS Streamable HTTP endpoint", "CAN'T VERIFY", 10,
                f"POST initialize returned HTTP {status}, but the response was not parseable as JSON or SSE-carried JSON.",
                "Return a valid MCP initialize JSON-RPC response over Streamable HTTP and retest.", DOCS["mcp"]
            ), endpoint, response
        return finding(
            "GCA-01", "Public HTTPS Streamable HTTP endpoint", "PASS", 10,
            f"POST initialize returned HTTP {status} with a parseable MCP response.",
            "No fix indicated. Confirm behavior again in Google Developer Mode.", DOCS["dev_mode"]
        ), endpoint, response
    return finding(
        "GCA-01", "Public HTTPS Streamable HTTP endpoint", "FAIL", 10,
        f"POST initialize did not produce a usable response: HTTP {status or 'no response'}; {response['error'] or 'unexpected status'}.",
        "Make the HTTPS endpoint publicly reachable and accept Streamable HTTP JSON-RPC POST requests.", DOCS["endpoint"]
    ), endpoint, response


def public_observation(response):
    return {
        "status": response.get("status"), "url": response.get("url"),
        "content_type": next((v for k, v in response.get("headers", {}).items() if k.lower() == "content-type"), None),
        "error": response.get("error"),
    }


def check_global_endpoint(data):
    declared = data.get("declared_endpoints")
    if not isinstance(declared, list) or not declared:
        return finding(
            "GCA-02", "One global endpoint", "CAN'T VERIFY", 9,
            "No declared_endpoints list was supplied, so regional endpoint sprawl cannot be checked.",
            "List every production MCP address in declared_endpoints. Use one global endpoint unless launching only in a single region.", DOCS["endpoint"]
        )
    normalized = {clean_url(item, https_only=True) for item in declared}
    normalized.discard(None)
    if len(normalized) != len(declared):
        return finding(
            "GCA-02", "One global endpoint", "FAIL", 9,
            "At least one declared endpoint is not a valid public HTTPS URL.",
            "Remove invalid addresses and declare the exact production endpoint set.", DOCS["endpoint"]
        )
    if len(normalized) == 1:
        return finding(
            "GCA-02", "One global endpoint", "PASS", 9,
            f"Exactly one production endpoint is declared: {next(iter(normalized))}.",
            "No fix indicated.", DOCS["endpoint"]
        )
    return finding(
        "GCA-02", "One global endpoint", "FAIL", 9,
        f"{len(normalized)} production endpoints are declared; Google does not support separate regional URLs for a global launch.",
        "Consolidate to one global MCP endpoint, or limit the launch to the single supported region and document that scope.", DOCS["endpoint"]
    )


def check_domain_token(data, endpoint, live, client, observations):
    if not endpoint:
        return finding(
            "GCA-03", "Domain verification token", "CAN'T VERIFY", 9,
            "The token URL cannot be derived without a valid endpoint.",
            "Fix the endpoint, then serve the Connected Console token at /.well-known/google-connected-apps with no redirect.", DOCS["endpoint"]
        )
    token_url = origin_for(endpoint) + "/.well-known/google-connected-apps"
    expected = data.get("expected_verification_token")
    if not live:
        return finding(
            "GCA-03", "Domain verification token", "CAN'T VERIFY", 9,
            f"Token location derived as {token_url}; live retrieval was not requested.",
            "Run with --live and supply expected_verification_token to verify the exact Connected Console token.", DOCS["endpoint"]
        )
    response = client.request(token_url, follow_redirects=False)
    observations["domain_token"] = public_observation(response)
    if response["status"] in (301, 302, 303, 307, 308):
        return finding(
            "GCA-03", "Domain verification token", "FAIL", 9,
            f"{token_url} returned redirect HTTP {response['status']}.",
            "Serve the token directly at the exact well-known path with HTTP 200 and no redirect.", DOCS["endpoint"]
        )
    if response["status"] != 200:
        return finding(
            "GCA-03", "Domain verification token", "FAIL", 9,
            f"{token_url} returned HTTP {response['status'] or 'no response'}.",
            "Publish the Connected Console verification token at the exact well-known path with HTTP 200 and no redirect.", DOCS["endpoint"]
        )
    parsed = decode_jsonish(response["body"])
    tokens = parsed.get("verification_tokens") if isinstance(parsed, dict) else None
    if not isinstance(tokens, list) or not all(isinstance(item, str) and item for item in tokens):
        return finding(
            "GCA-03", "Domain verification token", "FAIL", 9,
            "The well-known URL returned 200 but did not expose a non-empty verification_tokens array.",
            "Return the Connected Console token using Google's required JSON document shape.", DOCS["endpoint"]
        )
    if not expected:
        return finding(
            "GCA-03", "Domain verification token", "CAN'T VERIFY", 9,
            f"The URL returned HTTP 200 without redirect and exposed {len(tokens)} token value(s), but the expected console token was not supplied.",
            "Provide expected_verification_token and rerun to confirm the exact token, not only the document shape.", DOCS["endpoint"]
        )
    if expected not in tokens:
        return finding(
            "GCA-03", "Domain verification token", "FAIL", 9,
            "The well-known document loads, but it does not contain the supplied Connected Console token.",
            "Replace or append the exact current Connected Console token and retest without redirects.", DOCS["endpoint"]
        )
    return finding(
        "GCA-03", "Domain verification token", "PASS", 9,
        "The exact supplied token is present at the required well-known URL with HTTP 200 and no redirect.",
        "No fix indicated.", DOCS["endpoint"]
    )


def oauth_mode(data):
    mode = get_nested(data, "auth", "mode", default="unknown")
    return mode if isinstance(mode, str) else "unknown"


def fetch_json(client, url, observations, key):
    response = client.request(url)
    observations[key] = public_observation(response)
    return response, decode_jsonish(response["body"])


def check_oauth(data, live, client, observations):
    auth = data.get("auth") if isinstance(data.get("auth"), dict) else {}
    mode = oauth_mode(data)
    if mode == "none":
        return (
            finding(
                "GCA-04", "OAuth 2.1 and PKCE S256", "PASS", 8,
                "The app is explicitly declared unauthenticated, so OAuth and PKCE are not applicable.",
                "No OAuth fix indicated. Confirm the server exposes only data and actions suitable for unauthenticated access.", DOCS["oauth"]
            ),
            finding(
                "GCA-05", "OAuth discovery metadata", "PASS", 8,
                "The app is explicitly declared unauthenticated, so OAuth discovery documents are not applicable.",
                "No OAuth metadata fix indicated.", DOCS["oauth"]
            ),
        )
    if mode == "client-credentials":
        return (
            finding(
                "GCA-04", "OAuth 2.1 and PKCE S256", "PASS", 8,
                "The declared model is machine-to-machine client credentials; PKCE applies to authorization-code clients, not this flow.",
                "No PKCE fix indicated. Verify the client-credentials setup in Connected Console.", DOCS["oauth"]
            ),
            finding(
                "GCA-05", "OAuth discovery metadata", "CAN'T VERIFY", 8,
                "Machine-to-machine client settings cannot be confirmed from the public listing packet alone.",
                "Review the token endpoint and client credentials configuration in Connected Console without placing secrets in this audit file.", DOCS["oauth"]
            ),
        )
    if mode not in {"oauth2.1", "oauth2.0", "user-delegated", "unknown"}:
        unknown = f"Unrecognized auth.mode value: {mode}."
        return (
            finding("GCA-04", "OAuth 2.1 and PKCE S256", "CAN'T VERIFY", 8, unknown, "Use none, client-credentials, oauth2.0, oauth2.1, user-delegated, or unknown.", DOCS["oauth"]),
            finding("GCA-05", "OAuth discovery metadata", "CAN'T VERIFY", 8, unknown, "Declare the real authentication model and discovery URLs.", DOCS["oauth"]),
        )
    as_url = clean_url(auth.get("authorization_server_metadata_url"), https_only=True)
    if not as_url:
        issuer = clean_url(auth.get("issuer"), https_only=True)
        if issuer:
            as_url = issuer.rstrip("/") + "/.well-known/oauth-authorization-server"
    if not live or not as_url:
        reason = "Live OAuth discovery was not requested." if not live else "No authorization server metadata URL or issuer was supplied."
        return (
            finding(
                "GCA-04", "OAuth 2.1 and PKCE S256", "CAN'T VERIFY", 8, reason,
                "Supply the public authorization server metadata URL and run with --live. OAuth 2.1 authorization-code clients must advertise S256 PKCE; Google highly recommends OAuth 2.1.", DOCS["oauth"]
            ),
            finding(
                "GCA-05", "OAuth discovery metadata", "CAN'T VERIFY", 8, reason,
                "Supply the metadata URL and verify authorization_endpoint, token_endpoint, code response type, and registration details.", DOCS["oauth"]
            ),
        )
    response, metadata = fetch_json(client, as_url, observations, "authorization_server_metadata")
    if response["status"] != 200 or not isinstance(metadata, dict):
        evidence = f"Authorization server metadata returned HTTP {response['status'] or 'no response'} or invalid JSON."
        return (
            finding("GCA-04", "OAuth 2.1 and PKCE S256", "CAN'T VERIFY", 8, evidence, "Serve valid public authorization server metadata and retest.", DOCS["oauth"]),
            finding("GCA-05", "OAuth discovery metadata", "FAIL", 8, evidence, "Serve the required discovery document over HTTPS.", DOCS["oauth"]),
        )
    methods = metadata.get("code_challenge_methods_supported", [])
    if "S256" in methods:
        oauth_status = "PASS"
        oauth_evidence = "Authorization server metadata advertises PKCE S256."
        oauth_fix = "No PKCE fix indicated."
    elif mode == "oauth2.1":
        oauth_status = "FAIL"
        oauth_evidence = "The app declares OAuth 2.1, but discovery metadata does not advertise PKCE S256."
        oauth_fix = "Add S256 to code_challenge_methods_supported and implement verifier enforcement for the authorization-code flow."
    else:
        oauth_status = "CAN'T VERIFY"
        oauth_evidence = "Discovery metadata does not advertise S256. Google highly recommends OAuth 2.1; PKCE is mandatory for OAuth 2.1 and optional for OAuth 2.0."
        oauth_fix = "Prefer OAuth 2.1 with S256. If retaining OAuth 2.0, document the chosen Google-supported model and verify it in Developer Mode."
    required = {
        "authorization_endpoint": isinstance(metadata.get("authorization_endpoint"), str),
        "token_endpoint": isinstance(metadata.get("token_endpoint"), str),
        "response_types_supported includes code": "code" in metadata.get("response_types_supported", []),
    }
    registration = auth.get("client_registration", "unknown")
    if registration == "dynamic":
        required["registration_endpoint"] = isinstance(metadata.get("registration_endpoint"), str)
    missing = [key for key, value in required.items() if not value]
    metadata_status = "FAIL" if missing else "PASS"
    metadata_evidence = "Missing or invalid: " + ", ".join(missing) if missing else "Required authorization-code discovery fields are present."
    metadata_fix = "Add the missing fields to the public metadata document." if missing else "No discovery-field fix indicated."
    if registration not in {"dynamic", "manual"}:
        metadata_status = "CAN'T VERIFY" if metadata_status == "PASS" else metadata_status
        metadata_evidence += " Client registration mode was not declared as dynamic or manual."
        metadata_fix = "Declare client_registration as dynamic or manual; dynamic registration requires registration_endpoint."
    return (
        finding("GCA-04", "OAuth 2.1 and PKCE S256", oauth_status, 8, oauth_evidence, oauth_fix, DOCS["oauth"]),
        finding("GCA-05", "OAuth discovery metadata", metadata_status, 8, metadata_evidence, metadata_fix, DOCS["oauth"]),
    )


def live_tools(endpoint, init_response, client, observations):
    if not endpoint or not init_response or init_response.get("status") not in range(200, 300):
        return None
    session_id = next((v for k, v in init_response.get("headers", {}).items() if k.lower() == "mcp-session-id"), None)
    headers = {"Mcp-Session-Id": session_id} if session_id else {}
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    response = client.json_post(endpoint, payload, headers)
    observations["tools_list"] = public_observation(response)
    parsed = decode_jsonish(response["body"])
    if isinstance(parsed, dict):
        result = parsed.get("result")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            return result["tools"]
    return None


def tool_list(data, endpoint, init_response, live, client, observations):
    snapshot = data.get("tools_snapshot")
    if isinstance(snapshot, dict):
        snapshot = snapshot.get("tools")
    if isinstance(snapshot, list):
        return snapshot, "supplied tools_snapshot"
    if live:
        tools = live_tools(endpoint, init_response, client, observations)
        if isinstance(tools, list):
            return tools, "live tools/list"
    return None, "no usable tool inventory"


def check_tool_hints(tools, source_label):
    if tools is None:
        return finding(
            "GCA-06", "Explicit tool safety hints", "CAN'T VERIFY", 7,
            f"Tool annotations could not be inspected ({source_label}).",
            "Supply a sanitized tools_snapshot or permit an unauthenticated live tools/list response. Every tool needs an explicit readOnlyHint or destructiveHint.", DOCS["tools"]
        )
    problems = []
    for index, tool in enumerate(tools):
        name = tool.get("name", f"tool[{index}]") if isinstance(tool, dict) else f"tool[{index}]"
        annotations = tool.get("annotations") if isinstance(tool, dict) else None
        if not isinstance(annotations, dict):
            problems.append(f"{name}: missing annotations")
            continue
        read_only = annotations.get("readOnlyHint")
        destructive = annotations.get("destructiveHint")
        if not isinstance(read_only, bool) and not isinstance(destructive, bool):
            problems.append(f"{name}: neither hint is explicit")
        elif read_only is True and destructive is True:
            problems.append(f"{name}: contradictory readOnlyHint and destructiveHint")
    if problems:
        return finding(
            "GCA-06", "Explicit tool safety hints", "FAIL", 7,
            f"{len(problems)} of {len(tools)} tools need annotation review: " + "; ".join(problems[:8]),
            "Add explicit boolean annotations that accurately identify read-only versus state-changing/destructive behavior.", DOCS["tools"]
        )
    return finding(
        "GCA-06", "Explicit tool safety hints", "PASS", 7,
        f"All {len(tools)} tools expose an explicit readOnlyHint or destructiveHint in {source_label}.",
        "No annotation fix indicated. Validate actual behavior in Developer Mode.", DOCS["tools"]
    )


GENERIC_TOOL_NAMES = {"manage", "handle", "process", "execute", "run", "tool", "action", "do", "operate", "request"}


def schema_problems(schema, label):
    issues = []
    if not isinstance(schema, dict):
        return [f"{label} is missing or is not an object"]
    if schema.get("type") != "object":
        issues.append(f"{label}.type is not object")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        issues.append(f"{label}.properties is not an object")
        properties = {}
    required = schema.get("required", [])
    if required is not None and not isinstance(required, list):
        issues.append(f"{label}.required is not an array")
    elif isinstance(required, list):
        missing = [name for name in required if name not in properties]
        if missing:
            issues.append(f"{label}.required names absent from properties: {', '.join(map(str, missing))}")
    return issues


def name_is_vague(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{2,63}", name):
        return True
    tokens = [part.lower() for part in re.split(r"[_-]|(?<=[a-z])(?=[A-Z])", name) if part]
    return len(tokens) < 2 or all(token in GENERIC_TOOL_NAMES for token in tokens)


def check_schemas(tools, source_label):
    if tools is None:
        return finding(
            "GCA-07", "Tool schemas, names, and descriptions", "CAN'T VERIFY", 7,
            f"Tool schemas could not be inspected ({source_label}).",
            "Supply a sanitized tools_snapshot or obtain a live tools/list response, then fix invalid schemas and vague metadata.", DOCS["tools"]
        )
    issues = []
    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            issues.append(f"tool[{index}] is not an object")
            continue
        name = tool.get("name")
        label = name if isinstance(name, str) else f"tool[{index}]"
        if name_is_vague(name):
            issues.append(f"{label}: vague or invalid name")
        description = tool.get("description")
        if not isinstance(description, str) or len(description.split()) < 5:
            issues.append(f"{label}: description is missing or too vague")
        issues.extend(f"{label}: {item}" for item in schema_problems(tool.get("inputSchema"), "inputSchema"))
        if "outputSchema" in tool:
            issues.extend(f"{label}: {item}" for item in schema_problems(tool.get("outputSchema"), "outputSchema"))
    if issues:
        return finding(
            "GCA-07", "Tool schemas, names, and descriptions", "FAIL", 7,
            f"{len(issues)} issue(s) across {len(tools)} tools: " + "; ".join(issues[:10]),
            "Use strongly typed object schemas, valid required/property references, verb-noun tool names, and semantic descriptions that explain behavior and inputs.", DOCS["tools"]
        )
    return finding(
        "GCA-07", "Tool schemas, names, and descriptions", "PASS", 7,
        f"All {len(tools)} tools passed structural schema and metadata checks in {source_label}.",
        "No automated fix indicated. This is a structural pre-flight, not full JSON Schema conformance proof.", DOCS["tools"]
    )


def check_description(data):
    description = get_nested(data, "listing", "description")
    if not isinstance(description, str) or not description.strip():
        return finding("GCA-08", "Listing description under 30 words", "FAIL", 6, "Listing description is missing.", "Write a relevant description of 29 words or fewer.", DOCS["endpoint"])
    count = len(re.findall(r"\b[\w’'-]+\b", description))
    status = "PASS" if count < 30 else "FAIL"
    fix = "No fix indicated." if status == "PASS" else f"Cut at least {count - 29} word(s); Google requires fewer than 30 words."
    return finding("GCA-08", "Listing description under 30 words", status, 6, f"Description contains {count} words.", fix, DOCS["endpoint"])


def check_capabilities_prompts(data):
    listing = data.get("listing") if isinstance(data.get("listing"), dict) else {}
    capabilities = listing.get("capabilities")
    prompts = listing.get("example_prompts")
    app_name = data.get("app_name")
    problems = []
    if not isinstance(capabilities, list) or len([x for x in capabilities if isinstance(x, str) and x.strip()]) < 3:
        problems.append("fewer than 3 non-empty capabilities")
    if not isinstance(prompts, list) or len([x for x in prompts if isinstance(x, str) and x.strip()]) < 3:
        problems.append("fewer than 3 non-empty example prompts")
        starts = 0
    else:
        name = app_name.strip() if isinstance(app_name, str) else ''
        literal = re.escape(name)
        opening = re.compile(r'^@' + literal + r'(?![\w-])', re.I)
        mention = re.compile(r'(?<![\w-])' + literal + r'(?![\w-])', re.I)
        texts = [p.strip() for p in prompts if isinstance(p, str)]
        starts = sum(bool(name and opening.search(p)) for p in texts)
        if starts < 2:
            problems.append(f"only {starts} prompt(s) start with the app name")
        natural = sum(bool(name and not opening.search(p) and not mention.match(p) and mention.search(p)) for p in texts)
        if natural < 1:
            problems.append("no prompt mentions the app name naturally after the opening")
    if problems:
        return finding(
            "GCA-09", "Capabilities and example prompts", "FAIL", 6,
            "; ".join(problems) + ".",
            "Provide at least 3 capabilities and 3 prompts: 2 prompts starting with @ followed by the exact app name and 1 mentioning it naturally later.", DOCS["endpoint"]
        )
    return finding(
        "GCA-09", "Capabilities and example prompts", "PASS", 6,
        f"Listing includes {len(capabilities)} capabilities and {len(prompts)} prompts; {starts} start with the app name.",
        "No fix indicated.", DOCS["endpoint"]
    )


def image_info(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
        width, height = struct.unpack(">II", raw[16:24])
        return "PNG", width, height, len(raw)
    if raw.startswith(b"\xff\xd8"):
        i = 2
        while i + 9 < len(raw):
            if raw[i] != 0xFF:
                i += 1
                continue
            marker = raw[i + 1]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height, width = struct.unpack(">HH", raw[i + 5:i + 9])
                return "JPEG", width, height, len(raw)
            if i + 4 > len(raw):
                break
            length = struct.unpack(">H", raw[i + 2:i + 4])[0]
            i += 2 + length
    raise ValueError("not a supported PNG or JPEG")


def check_icon(data, input_path):
    icon = get_nested(data, "listing", "icon")
    if not isinstance(icon, str) or not icon:
        return finding("GCA-10", "512px icon up to 1,024 KB", "FAIL", 6, "No local icon path was supplied.", "Supply a 512 by 512 PNG or JPEG no larger than 1,024 KB.", DOCS["endpoint"])
    path = Path(icon)
    if not path.is_absolute():
        path = input_path.parent / path
    try:
        fmt, width, height, size = image_info(path)
    except (OSError, ValueError, struct.error) as exc:
        return finding("GCA-10", "512px icon up to 1,024 KB", "FAIL", 6, f"Icon could not be validated: {exc}.", "Use a readable 512 by 512 PNG or JPEG no larger than 1,024 KB.", DOCS["endpoint"])
    ok = width == 512 and height == 512 and size <= 1024 * 1024
    status = "PASS" if ok else "FAIL"
    fix = "No fix indicated." if ok else "Resize to exactly 512 by 512 and compress to at most 1,048,576 bytes."
    return finding("GCA-10", "512px icon up to 1,024 KB", status, 6, f"{fmt} icon is {width} by {height} and {size} bytes.", fix, DOCS["endpoint"])


def check_legal(data, live, client, observations):
    listing = data.get("listing") if isinstance(data.get("listing"), dict) else {}
    urls = {"Terms of Service": clean_url(listing.get("terms_url")), "Privacy Policy": clean_url(listing.get("privacy_url"))}
    missing = [name for name, url in urls.items() if not url]
    if missing:
        return finding("GCA-11", "Terms and Privacy links load", "FAIL", 6, "Missing or invalid URL(s): " + ", ".join(missing) + ".", "Provide public Terms of Service and Privacy Policy URLs.", DOCS["endpoint"])
    if not live:
        return finding("GCA-11", "Terms and Privacy links load", "CAN'T VERIFY", 6, "Both legal URLs are syntactically valid, but live retrieval was not requested.", "Run with --live to confirm both pages load publicly.", DOCS["endpoint"])
    failures = []
    evidence = []
    for name, url in urls.items():
        response = client.request(url)
        observations[f"legal_{name.lower().replace(' ', '_')}"] = public_observation(response)
        evidence.append(f"{name} HTTP {response['status'] or 'no response'}")
        if response["status"] is None or response["status"] >= 400:
            failures.append(name)
    status = "FAIL" if failures else "PASS"
    fix = "Make the failing legal page(s) publicly reachable." if failures else "No fix indicated."
    return finding("GCA-11", "Terms and Privacy links load", status, 6, "; ".join(evidence) + ".", fix, DOCS["endpoint"])


def normalize_text(value):
    return re.sub(r"\s+", " ", value.strip().lower()) if isinstance(value, str) else ""


def check_category(data):
    listing = data.get("listing") if isinstance(data.get("listing"), dict) else {}
    category = listing.get("category")
    required = listing.get("category_required_capabilities")
    actual = listing.get("capabilities")
    if not isinstance(category, str) or not category.strip():
        return finding("GCA-12", "Category capability coverage", "CAN'T VERIFY", 5, "No Connected Console category was supplied.", "Choose the category carefully; Google says it is immutable. Copy its predefined capability requirements into category_required_capabilities.", DOCS["endpoint"])
    if not isinstance(required, list) or not required:
        return finding("GCA-12", "Category capability coverage", "CAN'T VERIFY", 5, f"Category '{category}' is supplied, but its current Connected Console baseline capabilities are not.", "Copy the category's predefined capability requirements from Connected Console into category_required_capabilities and rerun. Do not infer them from recommendation pages.", DOCS["endpoint"])
    actual_set = {normalize_text(item) for item in actual or [] if isinstance(item, str)}
    missing = [item for item in required if normalize_text(item) not in actual_set]
    if missing:
        return finding("GCA-12", "Category capability coverage", "FAIL", 5, f"Category '{category}' is missing {len(missing)} required capability entry or entries: " + "; ".join(map(str, missing)), "Add the exact current category baseline capabilities shown by Connected Console.", DOCS["endpoint"])
    return finding("GCA-12", "Category capability coverage", "PASS", 5, f"All {len(required)} supplied baseline capabilities for '{category}' are present.", "No fix indicated. Reconfirm the immutable category and its baseline in Connected Console before submission.", DOCS["endpoint"])


def audit(data, input_path, live=False, lite=False, timeout=12.0):
    client = HttpClient(timeout)
    observations: dict[str, Any] = {}
    results: list[Finding] = []
    endpoint_result, endpoint, init_response = check_endpoint(data, live, client, observations)
    results.append(endpoint_result)
    if not lite:
        results.append(check_global_endpoint(data))
    results.append(check_domain_token(data, endpoint, live, client, observations))
    if not lite:
        results.extend(check_oauth(data, live, client, observations))
        tools, tool_source = tool_list(data, endpoint, init_response, live, client, observations)
        results.append(check_tool_hints(tools, tool_source))
        results.append(check_schemas(tools, tool_source))
    results.append(check_description(data))
    results.append(check_capabilities_prompts(data))
    results.append(check_icon(data, input_path))
    results.append(check_legal(data, live, client, observations))
    if not lite:
        results.append(check_category(data))
    results.sort(key=lambda item: (-item.priority, item.id))
    fails = sum(item.status == "FAIL" for item in results)
    unknowns = sum(item.status == "CAN'T VERIFY" for item in results)
    passes = sum(item.status == "PASS" for item in results)
    if fails:
        verdict = f"Fix {fails} item" + ("s" if fails != 1 else "")
    elif unknowns:
        verdict = f"Verify {unknowns} item" + ("s" if unknowns != 1 else "")
    else:
        verdict = "Ready"
    core = {
        "product": "Google Connected Apps Pre-flight Gate" if not lite else "Google Connected Apps Pre-flight Lite",
        "profile": "lite" if lite else "full",
        "rules_current_as_of": DOC_REVIEWED,
        "preview_warning": "Google Connected Apps is in preview. Re-check the linked Google documentation before submission.",
        "verdict": verdict,
        "counts": {"pass": passes, "fail": fails, "cant_verify": unknowns, "total": len(results)},
        "findings": [asdict(item) for item in results],
        "observations": observations,
        "limitations": [
            "This read-only pre-flight does not submit, register, approve, or change an MCP server or listing.",
            "A Ready result does not guarantee Google review approval, ranking, traffic, usage, or sales.",
            "Live tests are unauthenticated. Supply a sanitized tools_snapshot when authentication prevents tool inspection.",
            "Schema checks are structural and do not prove complete JSON Schema semantics or tool behavior.",
        ],
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    core["receipt_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()
    core["generated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return core


def markdown_report(report):
    lines = [
        f"# {report['product']}", "",
        f"**Result: {report['verdict']}**", "",
        f"Pass: {report['counts']['pass']} | Fail: {report['counts']['fail']} | Can't verify: {report['counts']['cant_verify']}", "",
        f"Rules reviewed: {report['rules_current_as_of']}. {report['preview_warning']}", "",
        "## Blocking order", "",
    ]
    for item in report["findings"]:
        lines.extend([
            f"### {item['status']} | {item['id']} | {item['title']}", "",
            item["evidence"], "",
            f"**Exact fix:** {item['fix']}", "",
            f"**Source:** {item['source']}", "",
        ])
    lines.extend(["## Connected Console copy-paste checklist", ""])
    for item in report["findings"]:
        box = "x" if item["status"] == "PASS" else " "
        lines.append(f"- [{box}] {item['id']} {item['title']}: {item['status']}")
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", f"Evidence receipt: `{report['receipt_sha256']}`", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Google Connected Apps pre-flight audit")
    parser.add_argument("input", type=Path, help="UTF-8 JSON app and listing packet")
    parser.add_argument("--live", action="store_true", help="Run public read-only HTTP checks")
    parser.add_argument("--lite", action="store_true", help="Run the free checks only: 1, 3, and 8-11")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)
    try:
        data = load_json(args.input)
        report = audit(data, args.input.resolve(), args.live, args.lite, args.timeout)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(encoded, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown_report(report), encoding="utf-8")
    print(f"{report['verdict']} | PASS {report['counts']['pass']} | FAIL {report['counts']['fail']} | CAN'T VERIFY {report['counts']['cant_verify']}")
    print(f"Receipt: {report['receipt_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
