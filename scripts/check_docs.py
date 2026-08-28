#!/usr/bin/env python3
"""
Verify that committed documentation statistics match the repository.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def get_test_count() -> int:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--collect-only",
            "-q",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(2)

    for line in reversed(result.stdout.splitlines()):
        match = re.search(r"(\d+) tests? collected", line)
        if match:
            return int(match.group(1))

    raise SystemExit("Unable to determine pytest test count.")


def get_current_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(
        encoding="utf-8",
    )

    match = re.search(
        r'(?m)^version\s*=\s*"([^"]+)"',
        pyproject,
    )

    if match is None:
        raise SystemExit("Unable to determine project version.")

    return match.group(1)


def get_readme_test_count() -> int:
    content = README.read_text(encoding="utf-8")

    match = re.search(
        r"- \*\*Tests:\*\* (\d+) passing",
        content,
    )

    if match is None:
        raise SystemExit(
            "README.md does not contain a test count."
        )

    return int(match.group(1))


def get_changelog_test_count(version: str) -> int:
    content = CHANGELOG.read_text(encoding="utf-8")

    match = re.search(
        rf"^## \[{re.escape(version)}\].*?"
        rf"(?=^## \[|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )

    if match is None:
        raise SystemExit(
            f"CHANGELOG.md does not contain version [{version}]."
        )

    section = match.group(0)

    count = re.search(
        r"(?m)^-\s+(\d+)\s+tests?\s+(?:total|passing)\s*$",
        section,
    )

    if count is None:
        raise SystemExit(
            f"Current CHANGELOG section [{version}] "
            "does not contain a test count."
        )

    return int(count.group(1))


def main() -> None:
    version = get_current_version()
    actual = get_test_count()
    readme = get_readme_test_count()
    changelog = get_changelog_test_count(version)

    failures: list[str] = []

    if readme != actual:
        failures.append(
            f"README.md says {readme} tests, "
            f"but pytest collected {actual}"
        )

    if changelog != actual:
        failures.append(
            f"CHANGELOG.md says {changelog} tests for {version}, "
            f"but pytest collected {actual}"
        )

    if failures:
        print("[FAIL] Documentation statistics are stale:")
        for failure in failures:
            print(f"  - {failure}")
        print()
        print(
            "Run: python scripts/generate_docs.py"
        )
        raise SystemExit(1)

    print(
        f"[OK] Documentation test count matches pytest: "
        f"{actual} tests"
    )


if __name__ == "__main__":
    main()