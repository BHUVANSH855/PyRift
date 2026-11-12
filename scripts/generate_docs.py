#!/usr/bin/env python3
"""
Generate project documentation statistics.

Run:

    python scripts/generate_docs.py

The script updates the current README statistics, the rule table,
docs/rules.md, and the current CHANGELOG test count so documentation does not
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
RULES_MD = ROOT / "docs" / "rules.md"


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


def _current_changelog_section(
    content: str,
    version: str,
) -> tuple[str, int, int]:
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

    return content[start:end], start, end


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
    section, start, end = _current_changelog_section(
        content,
        version,
    )

    updated_section, replacements = re.subn(
        r"^(- \*\*|-\s*)?(\d+)[ \t]+tests?[ \t]+(?:total|passing)[ \t]*$",
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

    return content[:start] + updated_section + content[end:]


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


def generate_rules_md() -> None:
    """Generate docs/rules.md from ALL_RULES and rule_metadata."""
    from pyrift import rule_metadata

    all_sorted = sorted(ALL_RULES, key=lambda r: r.rule_id)

    cpy_rules = [r for r in all_sorted if r.runtime == "cpython"]
    ppy_rules = [r for r in all_sorted if r.runtime == "pypy"]
    both_rules = [r for r in all_sorted if r.runtime == "both"]

    lines = [
        "# pyrift — Rule Reference",
        "",
        f"Complete documentation for all {len(all_sorted)} pyrift rules.",
        "",
        "---",
        "",
        "## How to read a finding",
        "",
        "A pyrift finding tells you:",
        "",
        "1. **What triggered it** — the rule ID and title (e.g. `CPY033 pathlib.Path.is_relative_to() requires Python 3.9+`)",
        "2. **How serious it is** — the severity level",
        "3. **How confident pyrift is** — the confidence level",
        "4. **Which runtimes are affected** — CPython, PyPy, or both",
        "5. **Which version range is affected** — the `Affected versions` field",
        "",
        "### Severity levels",
        "",
        "| Severity | Meaning | Recommended action |",
        "|---|---|---|",
        "| `ERROR` | Silent wrong behaviour — crash or data corruption on the affected version | Fix before shipping |",
        "| `WARNING` | Different behaviour — may or may not matter depending on your use case | Review and decide |",
        "| `INFO` | Worth knowing — low urgency, cosmetic or future-proofing concern | Fix when convenient |",
        "",
        "### Confidence levels",
        "",
        "| Confidence | Meaning |",
        "|---|---|",
        "| `HIGH` | Backed by official Python/PyPy docs or confirmed runtime probe |",
        "| `MEDIUM` | Strongly implied by docs or related behaviour |",
        "| `LOW` | Observed in practice — not formally documented |",
        "",
        "Rules with `LOW` confidence are still included because the behaviour is real,",
        "but you should verify independently before acting on them.",
        "",
        "---",
        "",
        "## What to do with a finding",
        "",
        "The general pattern for fixing a pyrift finding is:",
        "",
        "1. **Understand the version range** — check `Affected versions`. If your project's minimum supported Python",
        "   version is already higher than the affected range, the finding does not apply; add the version floor to",
        "   your `pyproject.toml` so pyrift can skip it automatically:",
        "",
        "   ```toml",
        "   [tool.pyrift]",
        '   minimum-python = "3.11"',
        "   ```",
        "",
        "2. **Apply the suggested fix** — each finding includes a `suggestion` field in the scan output. The fix is",
        "   almost always one of:",
        "   - Use a newer API that exists on all supported versions",
        "   - Guard the call with a `sys.version_info` check",
        "   - Add a compatibility shim (e.g. `tomli` for `tomllib`, `importlib_resources` for `importlib.resources`)",
        "",
        "3. **Suppress if intentional** — if you have deliberately decided to accept the incompatibility, add an",
        "   inline suppression so the finding does not recur:",
        "",
        "   ```python",
        "   result = path.is_relative_to(base)  # pyrift: ignore[CPY033]",
        "   ```",
        "",
        "   Or suppress all rules on a line:",
        "",
        "   ```python",
        "   some_code()  # pyrift: ignore",
        "   ```",
        "",
        "4. **Per-directory overrides** — for test directories or vendored code where different rules apply, use",
        "   `[[tool.pyrift.per-path]]` in `pyproject.toml`:",
        "",
        "   ```toml",
        "   [[tool.pyrift.per-path]]",
        '   path = "tests/**/*.py"',
        '   ignore = ["CPY033", "CPY034"]',
        "   ```",
        "",
        "---",
        "",
        "## Programmatic access",
        "",
        "```python",
        "import pyrift",
        "",
        "# Scan a directory",
        "result = pyrift.scan(\".\")",
        "print(result.breakdown())",
        '# {"high_confidence": 2, "medium_confidence": 0, "informational": 0, "analyzer_errors": 0}',
        "",
        "# Scan a source string",
        "findings = pyrift.scan_source(\"\"\"",
        "import pathlib",
        "p = pathlib.Path(\"/a\")",
        "p.is_relative_to(\"/b\")",
        "\"\"\")",
        "for f in findings:",
        "    print(f.rule_id, f.line, f.title)",
        "```",
        "",
        "---",
        "",
        "## CPython rules — version compatibility",
        "",
        "These rules detect code that behaves differently across CPython versions.",
        "",
    ]

    for rule in cpy_rules:
        lines.extend(_format_rule_section(rule, rule_metadata))

    lines.extend([
        "",
        "---",
        "",
        "## PyPy rules — runtime compatibility",
        "",
        "These rules detect code that behaves differently on PyPy vs CPython.",
        "",
    ])

    for rule in ppy_rules:
        lines.extend(_format_rule_section(rule, rule_metadata))

    if both_rules:
        lines.extend([
            "",
            "---",
            "",
            "## Cross-runtime rules — CPython & PyPy",
            "",
            "These rules apply to both CPython and PyPy.",
            "",
        ])
        for rule in both_rules:
            lines.extend(_format_rule_section(rule, rule_metadata))

    lines.append("")
    RULES_MD.write_text("\n".join(lines), encoding="utf-8")


def _whatsnew_url_from_ref(whatsnew_ref: str) -> str:
    """Convert a whatsnew_ref string to a full docs URL.

    Replicates the logic from ``Finding.whatsnew_url`` without needing a
    Finding instance.  Example: ``"3.13#pep-667-locals"`` →
    ``"https://docs.python.org/3/whatsnew/3.13.html#pep-667-locals"``
    """
    if not whatsnew_ref:
        return ""
    if "#" in whatsnew_ref:
        version, anchor = whatsnew_ref.split("#", 1)
        return f"https://docs.python.org/3/whatsnew/{version}.html#{anchor}"
    return f"https://docs.python.org/3/whatsnew/{whatsnew_ref}.html"


def _format_rule_section(rule, rule_metadata) -> list[str]:
    """Format a single rule as a rules.md section.

    Surfaces all authoritative metadata fields so that whatsnew_ref,
    gh_issue, affected_versions, contract_status, and intent_basis are
    visible in the public rule reference document.
    """
    meta = rule_metadata.RULE_METADATA.get(rule.rule_id, {})

    confidence = meta.get("confidence", "LOW")
    severity = rule.severity.title()

    runtime_label = {
        "cpython": "CPython",
        "pypy": "PyPy",
        "both": "CPython & PyPy",
    }.get(rule.runtime, rule.runtime.title())

    # --- header line -------------------------------------------------------
    lines = [
        f"### {rule.rule_id} — {rule.title}",
        "",
        f"**Severity:** {severity} | **Confidence:** {confidence.title()} | **Runtime:** {runtime_label}",
        "",
    ]

    # --- affected versions (from rule_metadata, not the rule class) --------
    affected_versions = meta.get("affected_versions", "")
    if affected_versions:
        lines.append(f"**Affected versions:** `{affected_versions}`")
        lines.append("")

    # --- CPython provenance links ------------------------------------------
    # gh_issue is stored as "cpython/issues/NNNNN"; the full GitHub URL is
    # https://github.com/python/{gh_issue}.  Display text uses only the
    # trailing issue number for readability.
    whatsnew_ref = meta.get("whatsnew_ref", "")
    gh_issue = meta.get("gh_issue", "")
    if whatsnew_ref or gh_issue:
        provenance_parts = []
        if whatsnew_ref:
            url = _whatsnew_url_from_ref(whatsnew_ref)
            version_label = whatsnew_ref.split("#")[0]
            provenance_parts.append(f"[What's New {version_label}]({url})")
        if gh_issue:
            issue_num = gh_issue.rsplit("/", 1)[-1]
            gh_url = f"https://github.com/python/{gh_issue}"
            provenance_parts.append(f"[cpython #{issue_num}]({gh_url})")
        lines.append("**References:** " + " · ".join(provenance_parts))
        lines.append("")

    # --- contract and intent basis -----------------------------------------
    # contract_status and intent_basis may be enum instances; use .value when
    # available so we emit the clean lowercase string, not the repr.
    def _enum_str(val: object) -> str:
        return getattr(val, "value", str(val)).replace("_", " ").title()

    contract_status = meta.get("contract_status")
    intent_basis = meta.get("intent_basis")
    if contract_status or intent_basis:
        contract_parts = []
        if contract_status:
            contract_parts.append(f"**Contract:** {_enum_str(contract_status)}")
        if intent_basis:
            contract_parts.append(f"**Basis:** {_enum_str(intent_basis)}")
        lines.append(" | ".join(contract_parts))
        lines.append("")

    # --- description from the rule's docstring -----------------------------
    doc = rule.__class__.__doc__ or ""
    doc_lines = [l.strip() for l in doc.split("\n") if l.strip()]
    if len(doc_lines) > 1:
        desc_lines = []
        for dl in doc_lines[1:]:
            if dl.startswith(("---", "Detects:")):
                break
            desc_lines.append(dl)
        if desc_lines:
            lines.append(" ".join(desc_lines))
            lines.append("")

    lines.append("---")
    return lines


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

    # Generate docs/rules.md
    generate_rules_md()
    print("docs/rules.md updated.")


if __name__ == "__main__":
    main()