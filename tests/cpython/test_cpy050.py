#!/usr/bin/env python3
"""
Generate rule counts and update README.md automatically.
Run: python scripts/generate_docs.py
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
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--tb=no", "-q"],
        capture_output=True, text=True, cwd=ROOT
    )
    for line in result.stdout.splitlines():
        if "passed" in line:
            nums = re.findall(r"\d+", line)
            if nums:
                return int(nums[0])
    return 0


def main() -> None:
    rules = pyrift.ALL_RULES
    cpy = [r for r in rules if r.rule_id.startswith("CPY")]
    ppy = [r for r in rules if r.rule_id.startswith("PPY")]
    total = len(rules)
    test_count = get_test_count()
    version = pyrift.__version__

    print(f"Rules: {total} ({len(cpy)} CPython + {len(ppy)} PyPy)")
    print(f"Tests: {test_count}")
    print(f"Version: {version}")

    content = README.read_text(encoding="utf-8")

    # Update project status section
    content = re.sub(
        r"- \*\*Version:\*\* [\d.]+",
        f"- **Version:** {version}",
        content,
    )
    content = re.sub(
        r"- \*\*Rules:\*\* \d+ \(\d+ CPython \+ \d+ PyPy\)",
        f"- **Rules:** {total} ({len(cpy)} CPython + {len(ppy)} PyPy)",
        content,
    )
    content = re.sub(
        r"- \*\*Tests:\*\* \d+ passing",
        f"- **Tests:** {test_count} passing",
        content,
    )
    # Update pre-commit rev
    content = re.sub(
        r"rev: v[\d.]+",
        f"rev: v{version}",
        content,
    )

    README.write_text(content, encoding="utf-8")
    print("README.md updated.")


if __name__ == "__main__":
    main()