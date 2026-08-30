#!/usr/bin/env python3
"""
Generate project documentation statistics.

Run:

    python scripts/generate_docs.py

The script updates the current README statistics, the rule table,
and the current CHANGELOG test count so documentation does not
silently drift from the repository.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pyrift
from pyrift.scanner import ALL_RULES

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def get_test_count() -> int:
    """Return the number of collected pytest tests."""
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
        raise RuntimeError(
            "pytest test collection failed:\n"
            f"{result.stdout}\n{result.stderr}"
        )

    for line in reversed(result.stdout.splitlines()):
        match = re.search(r"(\d+) tests? collected", line)
        if match:
            return int(match.group(1))

    raise RuntimeError(
        "unable to determine pytest test count from collection output"
    )


def _current_changelog_section(content: str, version: str) -> tuple[str, str]:
    """Return the current version section and its boundaries."""
    match = re.search(
        rf"^## \[{re.escape(version)}\].*$",
        content,
        re.MULTILINE,
    )

    if match is None:
        raise RuntimeError(
            f"CHANGELOG.md does not contain version [{version}]"
        )

    start = match.start()

    next_heading = re.search(
        r"^## \[",
        content[match.end():],
        re.MULTILINE,
    )

    if next_heading is None:
        end = len(content)
    else:
        end = match.end() + next_heading.start()

    return content[start:end], content[:start] + content[end:]


def update_readme(
    content: str,
    version: str,
    total: int,
    cpy: int,
    ppy: int,
    both: int,
    test_count: int,
) -> str:
    content = re.sub(
        r"- \*\*Version:\*\* [\d.]+",
        f"- **Version:** {version}",
        content,
        count=1,
    )

    content = re.sub(
        r"- \*\*Rules:\*\*.*",
        (
            f"- **Rules:** {total} total "
            f"({cpy} CPython + "
            f"{ppy} PyPy + "
            f"{both} cross-runtime)"
        ),
        content,
        count=1,
    )

    content = re.sub(
        r"- \*\*Tests:\*\* \d+ passing",
        f"- **Tests:** {test_count} passing",
        content,
        count=1,
    )

    content = re.sub(
        r"rev: v[\d.]+",
        f"rev: v{version}",
        content,
    )

    return content


def update_changelog(
    content: str,
    version: str,
    test_count: int,
) -> str:
    section, outside = _current_changelog_section(
        content,
        version,
    )

    updated_section, replacements = re.subn(
        r"^(- \*\*|\-\s*)?(\d+)\s+tests?\s+(?:total|passing)\s*$",
        lambda match: f"- {test_count} tests total",
        section,
        count=1,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    if replacements == 0:
        updated_section = section.rstrip() + (
            f"\n\n### Verification\n"
            f"- {test_count} tests total\n"
        )

    return outside[:0] + updated_section + outside


def generate_rule_table() -> str:
    """Generate a Markdown rule index table from ALL_RULES.

    Uses marker comments so the README section can be reliably regenerated:
        <!-- BEGIN GENERATED RULE INDEX -->
        ...
        <!-- END GENERATED RULE INDEX -->
    """
    all_sorted = sorted(ALL_RULES, key=lambda r: r.rule_id)
    lines = [
        "<!-- BEGIN GENERATED RULE INDEX -->",
        "| Rule | Title | Runtime |",
        "|------|-------|---------|",
    ]
    for rule in all_sorted:
        # Escape pipe characters to avoid breaking the Markdown table
        title = rule.title.replace("|", r"\|")
        lines.append(f"| {rule.rule_id} | {title} | {rule.runtime} |")
    lines.append("<!-- END GENERATED RULE INDEX -->")
    return "\n".join(lines)


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

    readme_content = README.read_text(
        encoding="utf-8",
    )

    readme_content = update_readme(
        readme_content,
        version,
        total,
        len(cpy),
        len(ppy),
        len(both),
        test_count,
    )

    # Auto-generate rule table using markers
    rule_table = generate_rule_table()
    start_marker = "<!-- BEGIN GENERATED RULE INDEX -->"
    end_marker = "<!-- END GENERATED RULE INDEX -->"
    if start_marker in readme_content and end_marker in readme_content:
        start_idx = readme_content.find(start_marker)
        end_idx = readme_content.find(end_marker) + len(end_marker)
        readme_content = readme_content[:start_idx] + rule_table + readme_content[end_idx:]
    else:
        raise RuntimeError(
            "README.md is missing GENERATED RULE INDEX markers.\n"
            "Expected:\n"
            "  <!-- BEGIN GENERATED RULE INDEX -->\n"
            "  <!-- END GENERATED RULE INDEX -->\n"
        )

    README.write_text(
        readme_content,
        encoding="utf-8",
    )

    changelog_content = CHANGELOG.read_text(
        encoding="utf-8",
    )

    changelog_content = update_changelog(
        changelog_content,
        version,
        test_count,
    )

    CHANGELOG.write_text(
        changelog_content,
        encoding="utf-8",
    )

    print("README.md updated.")
    print("CHANGELOG.md updated.")


if __name__ == "__main__":
    main()