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
            "files_scanned":        result.files_scanned,
            "total_findings":       len(result.findings),
            "errors":               len(result.errors),
            "warnings":             len(result.warnings),
            "baseline_suppressed":  result.baseline_suppressed,
            "score":                result.score,
            "rule_errors":          len(result.rule_errors),
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
    lines.append(f"| Files scanned        | {result.files_scanned} |")
    lines.append(f"| Errors               | {len(result.errors)} |")
    lines.append(f"| Warnings             | {len(result.warnings)} |")
    lines.append(f"| Baseline suppressed  | {result.baseline_suppressed} |")
    lines.append(f"| Health score         | {result.score} / 100 |")
    lines.append(f"| Rule execution errors| {len(result.rule_errors)} |")
    lines.append("")

    if not result.findings:
        if result.rule_errors:
            lines.append(
                "⚠️ **No behaviour findings were produced, but rule execution "
                f"failed {len(result.rule_errors)} time(s).**\n"
            )
        else:
            msg = "✅ **No behaviour differences detected.**"
            if result.baseline_suppressed:
                msg += (
                    f"\n\n> ℹ️ Baseline suppressed "
                    f"{result.baseline_suppressed} known finding(s)."
                )
            lines.append(msg + "\n")
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
        if result.rule_errors:
            lines.append(
                f"⚠️  No findings produced — {result.files_scanned} file(s) scanned, "
                f"but {len(result.rule_errors)} rule execution error(s) occurred."
            )
        else:
            msg = f"✅  No issues found — {result.files_scanned} file(s) scanned."
            if result.baseline_suppressed:
                msg += f"\nBaseline suppressed: {result.baseline_suppressed} finding(s)"
            lines.append(msg)
        return "\n".join(lines)

    for f in result.findings:
        lines.append(str(f))
        if f.suggestion:
            lines.append(f"    → {f.suggestion}")
    lines.append("")
    summary = (
        f"Scanned {result.files_scanned} file(s). "
        f"Found {len(result.errors)} error(s), "
        f"{len(result.warnings)} warning(s). "
        f"Score: {result.score}/100"
    )
    if result.rule_errors:
        summary += f"; {len(result.rule_errors)} rule execution error(s)"
    if result.baseline_suppressed:
        summary += f" (baseline suppressed: {result.baseline_suppressed})"
    lines.append(summary)
    return "\n".join(lines)