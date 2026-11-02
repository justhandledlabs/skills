#!/usr/bin/env python3
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

import google_connected_apps_preflight as gate


def png_bytes(width, height, rgb=(242, 13, 61)):
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


class FakeClient:
    mode = "pass"

    def __init__(self, timeout=12.0):
        self.timeout = timeout

    def json_post(self, url, payload, extra_headers=None):
        if self.mode == "fail":
            return {"status": 405, "url": url, "headers": {}, "body": b"", "error": "Method Not Allowed"}
        body = {"jsonrpc": "2.0", "id": payload.get("id"), "result": {"protocolVersion": "2025-03-26"}}
        return {"status": 200, "url": url, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body).encode(), "error": None}

    def request(self, url, method="GET", data=None, headers=None, follow_redirects=True):
        if self.mode == "fail":
            status = 302 if "google-connected-apps" in url else 404
            return {"status": status, "url": url, "headers": {}, "body": b"", "error": "failure fixture"}
        if "google-connected-apps" in url:
            body = json.dumps({"verification_tokens": ["demo-token-2026"]}).encode()
        else:
            body = b"ok"
        return {"status": 200, "url": url, "headers": {"Content-Type": "application/json"}, "body": body, "error": None}


def valid_packet(icon_name):
    return {
        "app_name": "Demo Records",
        "endpoint": "https://demo-records.example/mcp",
        "declared_endpoints": ["https://demo-records.example/mcp"],
        "expected_verification_token": "demo-token-2026",
        "auth": {"mode": "none"},
        "listing": {
            "description": "Demo Records finds approved project records and prepares cited summaries.",
            "capabilities": ["Find approved records", "Summarize selected records", "Cite source records"],
            "example_prompts": [
                "Demo Records, find the latest approved project brief.",
                "Demo Records, summarize the approved decisions for this project.",
                "Use Demo Records to cite the source records for this summary.",
            ],
            "icon": icon_name,
            "terms_url": "https://demo-records.example/terms",
            "privacy_url": "https://demo-records.example/privacy",
            "category": "Productivity",
            "category_required_capabilities": ["Find approved records"],
        },
        "tools_snapshot": {"tools": [{
            "name": "find_approved_records",
            "description": "Find approved project records matching the supplied query.",
            "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            "annotations": {"readOnlyHint": True, "destructiveHint": False},
        }]},
    }


class PreflightTests(unittest.TestCase):
    def test_all_twelve_checks_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "icon.png").write_bytes(png_bytes(512, 512))
            packet = valid_packet("icon.png")
            FakeClient.mode = "pass"
            with mock.patch.object(gate, "HttpClient", FakeClient):
                report = gate.audit(packet, root / "input.json", live=True)
            self.assertEqual("Ready", report["verdict"])
            self.assertEqual({"pass": 12, "fail": 0, "cant_verify": 0, "total": 12}, report["counts"])

    def test_failures_are_ordered_and_specific(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "icon.png").write_bytes(png_bytes(128, 128))
            packet = valid_packet("icon.png")
            packet["declared_endpoints"].append("https://eu.demo-records.example/mcp")
            packet["listing"]["description"] = " ".join(["word"] * 35)
            packet["listing"]["capabilities"] = ["One"]
            packet["listing"]["example_prompts"] = ["Try it"]
            packet["listing"]["category_required_capabilities"] = ["Missing capability"]
            packet["tools_snapshot"]["tools"][0] = {"name": "manage", "description": "Does things", "inputSchema": {"type": "string"}}
            FakeClient.mode = "fail"
            with mock.patch.object(gate, "HttpClient", FakeClient):
                report = gate.audit(packet, root / "input.json", live=True)
            self.assertTrue(report["verdict"].startswith("Fix "))
            failed = {item["id"] for item in report["findings"] if item["status"] == "FAIL"}
            self.assertTrue({"GCA-01", "GCA-02", "GCA-03", "GCA-06", "GCA-07", "GCA-08", "GCA-09", "GCA-10", "GCA-11", "GCA-12"}.issubset(failed))
            self.assertEqual("GCA-01", report["findings"][0]["id"])

    def test_lite_profile_only_runs_six_requested_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "icon.png").write_bytes(png_bytes(512, 512))
            FakeClient.mode = "pass"
            with mock.patch.object(gate, "HttpClient", FakeClient):
                report = gate.audit(valid_packet("icon.png"), root / "input.json", live=True, lite=True)
            self.assertEqual("Ready", report["verdict"])
            self.assertEqual(6, report["counts"]["total"])

    def test_optional_get_405_is_not_used_as_transport_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "icon.png").write_bytes(png_bytes(512, 512))
            FakeClient.mode = "pass"
            with mock.patch.object(gate, "HttpClient", FakeClient):
                report = gate.audit(valid_packet("icon.png"), root / "input.json", live=True)
            item = next(item for item in report["findings"] if item["id"] == "GCA-01")
            self.assertEqual("PASS", item["status"])
            self.assertIn("POST initialize", item["evidence"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

