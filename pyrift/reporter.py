"""
pyrift.reporter
~~~~~~~~~~~~~~~
Formats ScanResult into JSON, Markdown, or plain text.
"""
from __future__ import annotations

import json

from .finding import Severity
from .scanner import ScanResult


def to_json(result: ScanResult, indent: int = 2) -> str:
    data = {
        "summary": {
            "files_scanned":  result.files_scanned,
            "total_findings": len(result.findings),
            "errors":         len(result.errors),
            "warnings":       len(result.warnings),
            "score":          result.score,
        },
        "findings": [f.to_dict() for f in result.findings],
    }
    return json.dumps(data, indent=indent)


def to_markdown(result: ScanResult) -> str:
    lines: list[str] = []
    lines.append("# pyrift — Scan Report\n")
    lines.append("## Summary\n")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Files scanned | {result.files_scanned} |")
    lines.append(f"| Errors        | {len(result.errors)} |")
    lines.append(f"| Warnings      | {len(result.warnings)} |")
    lines.append(f"| Health score  | {result.score} / 100 |")
    lines.append("")

    if not result.findings:
        lines.append("✅ **No behaviour differences detected.**\n")
        return "\n".join(lines)

    for sev in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        group = [f for f in result.findings if f.severity == sev]
        if not group:
            continue
        emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}[sev.value]
        lines.append(f"## {emoji} {sev.value.capitalize()}s ({len(group)})\n")
        for f in group:
            lines.append(f"### `{f.rule_id}` — {f.title}")
            lines.append(f"**Location:** `{f.file}:{f.line}`  ")
            lines.append(f"**Runtime:** `{f.runtime.value}`  ")
            if f.affected_from:
                lines.append(
                    f"**Affects:** Python {f.affected_from}"
                    + (f" – {f.affected_until}" if f.affected_until else "+")
                )
            lines.append(f"\n{f.description}\n")
            if f.suggestion:
                lines.append(f"💡 **Fix:** {f.suggestion}\n")
            if f.docs_url:
                lines.append(f"📖 [Docs]({f.docs_url})\n")
            lines.append("---")

    return "\n".join(lines)


def to_text(result: ScanResult) -> str:
    lines: list[str] = []
    if not result.findings:
        lines.append(
            f"✅  No issues found — {result.files_scanned} file(s) scanned."
        )
        return "\n".join(lines)

    for f in result.findings:
        lines.append(str(f))
        if f.suggestion:
            lines.append(f"    → {f.suggestion}")
    lines.append("")
    lines.append(
        f"Scanned {result.files_scanned} file(s). "
        f"Found {len(result.errors)} error(s), "
        f"{len(result.warnings)} warning(s). "
        f"Score: {result.score}/100"
    )
    return "\n".join(lines)