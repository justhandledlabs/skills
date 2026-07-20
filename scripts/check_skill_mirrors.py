#!/usr/bin/env python3
"""Verify portable skills and Claude marketplace copies are identical."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTABLE_ROOT = ROOT / "skills"
PLUGINS_ROOT = ROOT / "plugins"


def files_by_relative_path(directory: Path) -> dict[Path, Path]:
    return {
        path.relative_to(directory): path
        for path in directory.rglob("*")
        if path.is_file()
    }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    problems: list[str] = []
    portable_names = {path.name for path in PORTABLE_ROOT.iterdir() if path.is_dir()}
    plugin_names = {path.name for path in PLUGINS_ROOT.iterdir() if path.is_dir()}

    if portable_names != plugin_names:
        missing_portable = sorted(plugin_names - portable_names)
        missing_plugins = sorted(portable_names - plugin_names)
        if missing_portable:
            problems.append(f"Missing portable skills: {', '.join(missing_portable)}")
        if missing_plugins:
            problems.append(f"Missing plugin wrappers: {', '.join(missing_plugins)}")

    for name in sorted(portable_names & plugin_names):
        portable = PORTABLE_ROOT / name
        plugin_copy = PLUGINS_ROOT / name / "skills" / name
        if not plugin_copy.is_dir():
            problems.append(f"Missing plugin skill directory: {plugin_copy.relative_to(ROOT)}")
            continue

        portable_files = files_by_relative_path(portable)
        plugin_files = files_by_relative_path(plugin_copy)
        if portable_files.keys() != plugin_files.keys():
            only_portable = sorted(str(path) for path in portable_files.keys() - plugin_files.keys())
            only_plugin = sorted(str(path) for path in plugin_files.keys() - portable_files.keys())
            if only_portable:
                problems.append(f"{name}: portable-only files: {', '.join(only_portable)}")
            if only_plugin:
                problems.append(f"{name}: plugin-only files: {', '.join(only_plugin)}")
            continue

        for relative_path in sorted(portable_files):
            if digest(portable_files[relative_path]) != digest(plugin_files[relative_path]):
                problems.append(f"{name}: content differs at {relative_path}")

    if problems:
        print("Skill mirror check failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(f"Skill mirror check passed for {len(portable_names)} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
