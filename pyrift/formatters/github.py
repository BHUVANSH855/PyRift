"""GitHub Actions workflow-command formatter.

Emits one ``::error`` or ``::warning`` annotation per finding so that
GitHub shows inline diff comments on pull requests and in the Actions
log.  ``::notice`` is used for INFO-severity findings.

Reference:
  https://docs.github.com/en/actions/writing-workflows/
  choosing-what-your-workflow-does/
  workflow-commands-for-github-actions#setting-an-error-message
"""

from __future__ import annotations

from ..finding import Finding, Severity
from ..scanner import ScanResult


def _escape(value: str) -> str:
    """Escape special characters for GitHub workflow-command values."""
    return (
        value
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def _annotation_level(finding: Finding) -> str:
    """Map PyRift severity to a GitHub annotation level."""
    if finding.severity == Severity.ERROR:
        return "error"
    if finding.severity == Severity.WARNING:
        return "warning"
    return "notice"


def to_github_annotations(result: ScanResult) -> str:
    """Return GitHub Actions workflow commands for all findings.

    Each finding becomes one ``::error``, ``::warning``, or ``::notice``
    line.  GitHub renders these as inline annotations in the pull-request
    diff and in the Actions log.

    If there are no findings an empty string is returned (no output is
    the conventional signal for a clean run).
    """
    if not result.findings:
        return ""

    lines: list[str] = []
    for finding in result.findings:
        level = _annotation_level(finding)
        file_path = _escape(str(finding.file))
        title = _escape(f"{finding.rule_id}: {finding.title}")
        # Description is the most useful annotation body; fall back to title.
        message = _escape(finding.description or finding.title)

        param_parts = [f"file={file_path}", f"line={finding.line}"]
        if finding.col:
            param_parts.append(f"col={finding.col}")
        param_parts.append(f"title={title}")
        params = ",".join(param_parts)

        lines.append(f"::{level} {params}::{message}")

    return "\n".join(lines)
