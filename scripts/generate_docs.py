#!/usr/bin/env python3
"""
Generate project documentation statistics.

Run:
    python scripts/generate_docs.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pyrift

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"


def get_test_count() -> int:
    import re as _re
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--tb=no", "-q"],
        capture_output=True, text=True, cwd=ROOT, check=False,
    )
    for line in result.stdout.splitlines():
        m = _re.search(r"(\d+) passed", line)
        if m:
            return int(m.group(1))
    return 0


def main() -> None:
    rules = pyrift.ALL_RULES

    cpy = [
        rule
        for rule in rules
        if rule.runtime == "cpython"
    ]

    ppy = [
        rule
        for rule in rules
        if rule.runtime == "pypy"
    ]

    both = [
        rule
        for rule in rules
        if rule.runtime == "both"
    ]

    total = len(rules)
    test_count = get_test_count()
    version = pyrift.__version__

    print(
        f"Rules: {total} "
        f"({len(cpy)} CPython + "
        f"{len(ppy)} PyPy + "
        f"{len(both)} cross-runtime)"
    )
    print(f"Tests: {test_count}")
    print(f"Version: {version}")

    content = README.read_text(
        encoding="utf-8",
    )

    content = re.sub(
        r"- \*\*Version:\*\* [\d.]+",
        f"- **Version:** {version}",
        content,
    )

    content = re.sub(
        r"- \*\*Rules:\*\*.*",
        (
            f"- **Rules:** {total} total "
            f"({len(cpy)} CPython + "
            f"{len(ppy)} PyPy + "
            f"{len(both)} cross-runtime)"
        ),
        content,
    )

    content = re.sub(
        r"- \*\*Tests:\*\* \d+ passing",
        f"- **Tests:** {test_count} passing",
        content,
    )

    content = re.sub(
        r"rev: v[\d.]+",
        f"rev: v{version}",
        content,
    )

    README.write_text(
        content,
        encoding="utf-8",
    )

    print("README.md updated.")


if __name__ == "__main__":
    main()