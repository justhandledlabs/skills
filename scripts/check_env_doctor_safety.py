#!/usr/bin/env python3
"""Static regression checks for Env Doctor's safety contract."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "env-doctor-free" / "SKILL.md"
CHECKS = ROOT / "skills" / "env-doctor-free" / "references" / "checks.md"
FIXTURES = ROOT / "skills" / "env-doctor-free" / "references" / "safety-fixtures.md"


def main() -> int:
    skill = SKILL.read_text(encoding="utf-8")
    checks = CHECKS.read_text(encoding="utf-8")
    fixtures = FIXTURES.read_text(encoding="utf-8")
    combined = f"{skill}\n{checks}"

    required = {
        "v1.2 metadata": "version: 1.2.0",
        "explicit stop approval": "explicit approval",
        "Windows ownership inspection": "Get-Process",
        "POSIX ownership inspection": "ps -p <PID>",
        "secret-value prohibition": "Never print",
        "key-only env evidence": "key names",
        "PowerShell output contract": "powershell",
        "canary fixture": "sk-jhl-do-not-echo-9f7c",
    }
    sources = {**{label: combined for label in required}, "canary fixture": fixtures}
    forbidden = {
        "unconditional POSIX force-kill": "\nkill -9 ",
        "unconditional PowerShell force-kill": "\nStop-Process -Force ",
        "raw POSIX env display": "\ncat .env",
        "raw PowerShell env display": "\nGet-Content .env",
    }

    problems = [
        f"missing requirement: {label}"
        for label, marker in required.items()
        if marker not in sources[label]
    ]
    problems.extend(
        f"unsafe example present: {label}"
        for label, marker in forbidden.items()
        if marker in combined
    )

    if problems:
        print("Env Doctor safety check failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Env Doctor safety check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
