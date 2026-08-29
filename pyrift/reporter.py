"""
pyrift.reporter
~~~~~~~~~~~~~~
Formats ScanResult into JSON, Markdown, plain text, or SARIF 2.1.0.
"""
from __future__ import annotations

import json
from collections import OrderedDict

from .finding import Severity
from .scanner import ScanResult


def to_json(result: ScanResult, indent: int = 2) -> str:
    data = {
        "summary": {
            "files_scanned": result.files_scanned,
            "total_findings": len(result.findings),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "baseline_suppressed": result.baseline_suppressed,
            "score": result.score,
            "rule_errors": len(result.rule_errors),
        },
        "findings": [f.to_dict() for f in result.findings],
    }
    return json.dumps(data, indent=indent)


def to_markdown(result: ScanResult) -> str:
    lines: list[str] = []

    lines.append("# pyrift -- Scan Report\n")
    lines.append("## Summary\n")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Files scanned         | {result.files_scanned} |")
    lines.append(f"| Errors                | {len(result.errors)} |")
    lines.append(f"| Warnings              | {len(result.warnings)} |")
    lines.append(
        f"| Baseline suppressed   | {result.baseline_suppressed} |"
    )
    lines.append(f"| Health score          | {result.score} / 100 |")
    lines.append(
        f"| Rule execution errors | {len(result.rule_errors)} |"
    )
    lines.append("")

    if not result.findings:
        if result.rule_errors:
            lines.append(
                "[WARN] **No behaviour findings were produced, but rule "
                f"execution failed {len(result.rule_errors)} time(s).**\n"
            )
        else:
            msg = "[OK] **No behaviour differences detected.**"
            if result.baseline_suppressed:
                msg += (
                    f"\n\n> [INFO] Baseline suppressed "
                    f"{result.baseline_suppressed} known finding(s)."
                )
            lines.append(msg + "\n")

        return "\n".join(lines)

    for sev in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        group = [
            finding
            for finding in result.findings
            if finding.severity == sev
        ]

        if not group:
            continue

        marker = {
            "error": "[ERROR]",
            "warning": "[WARN]",
            "info": "[INFO]",
        }[sev.value]

        lines.append(
            f"## {marker} {sev.value.capitalize()}s ({len(group)})\n"
        )

        for finding in group:
            lines.append(
                f"### `{finding.rule_id}` -- {finding.title}"
            )
            lines.append(
                f"**Location:** `{finding.file}:{finding.line}`  "
            )
            lines.append(
                f"**Runtime:** `{finding.runtime.value}`  "
            )
            lines.append(
                f"**Confidence:** `{finding.confidence.value}`  "
            )
            lines.append(
                f"**Evidence:** `{finding.evidence_type.value}`"
                + (
                    f" (`{finding.evidence_source}`)"
                    if finding.evidence_source
                    else ""
                )
                + "  "
            )

            if finding.affected_from:
                lines.append(
                    f"**Affects:** Python {finding.affected_from}"
                    + (
                        f" – {finding.affected_until}"
                        if finding.affected_until
                        else "+"
                    )
                )

            lines.append(f"\n{finding.description}\n")

            if finding.suggestion:
                lines.append(
                    f"💡 **Fix:** {finding.suggestion}\n"
                )

            if finding.docs_url:
                lines.append(
                    f"📖 [Docs]({finding.docs_url})\n"
                )

            lines.append("---")

    return "\n".join(lines)


def to_text(result: ScanResult) -> str:
    lines: list[str] = []

    if not result.findings:
        if result.rule_errors:
            lines.append(
                f"[WARN]  No findings produced -- "
                f"{result.files_scanned} file(s) scanned, but "
                f"{len(result.rule_errors)} rule execution error(s) occurred."
            )
        else:
            msg = (
                f"[OK]  No issues found -- "
                f"{result.files_scanned} file(s) scanned."
            )

            if result.baseline_suppressed:
                msg += (
                    f"\nBaseline suppressed: "
                    f"{result.baseline_suppressed} finding(s)"
                )

            lines.append(msg)

        return "\n".join(lines)

    for finding in result.findings:
        lines.append(str(finding))
        lines.append(
            f"    evidence: {finding.evidence_type.value}"
            + (
                f" ({finding.evidence_source})"
                if finding.evidence_source
                else ""
            )
        )

        if finding.suggestion:
            lines.append(
                f"    -> {finding.suggestion}"
            )

    lines.append("")

    summary = (
        f"Scanned {result.files_scanned} file(s). "
        f"Found {len(result.errors)} error(s), "
        f"{len(result.warnings)} warning(s). "
        f"Score: {result.score}/100"
    )

    if result.rule_errors:  # pragma: no branch
        summary += (
            f"; {len(result.rule_errors)} "
            f"rule execution error(s)"
        )

    if result.baseline_suppressed:  # pragma: no branch
        summary += (
            f" (baseline suppressed: "
            f"{result.baseline_suppressed})"
        )

    lines.append(summary)
    return "\n".join(lines)


def to_sarif(result: ScanResult) -> str:
    """Generate a SARIF 2.1.0 JSON report from a ScanResult."""
    from . import __version__

    rules_map: dict[str, dict] = OrderedDict()
    sarif_results: list[dict] = []

    for finding in result.findings:
        rule_id = finding.rule_id

        if rule_id not in rules_map:
            rules_map[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": finding.title},
                "helpUri": finding.docs_url or "",
                "properties": {
                    "tags": [
                        finding.severity.value,
                        finding.confidence.value,
                        finding.runtime.value,
                    ],
                    "category": getattr(finding, "category", "compatibility"),
                },
            }

        message_text = finding.title
        if finding.description:
            message_text += f" — {finding.description}"

        start_line = max(1, finding.line or 1)
        start_column = max(1, finding.col or 1)

        physical_location = {
            "artifactLocation": {"uri": finding.file},
            "region": {
                "startLine": start_line,
                "startColumn": start_column,
            },
        }

        sarif_properties: dict[str, str | None] = {
            "confidence": finding.confidence.value,
            "evidence_type": finding.evidence_type.value,
            "runtime": finding.runtime.value,
            "affected_from": finding.affected_from or None,
            "affected_until": finding.affected_until or None,
            "suggestion": finding.suggestion or None,
            "category": getattr(finding, "category", "compatibility"),
        }

        sarif_results.append({
            "ruleId": rule_id,
            "message": {"text": message_text},
            "locations": [
                {"physicalLocation": physical_location}
            ],
            "properties": sarif_properties,
        })

    sarif: dict = {
        "$schema": (
            "https://raw.githubusercontent.com/oasis-tcs/sarif-spec"
            "/master/Schemata/sarif-schema-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "pyrift",
                        "version": __version__,
                        "rules": list(rules_map.values()),
                    },
                },
                "results": sarif_results,
            },
        ],
    }

    return json.dumps(sarif, indent=2)