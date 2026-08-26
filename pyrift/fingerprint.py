"""
pyrift.fingerprint
~~~~~~~~~~~~~~~~~~
Stable identities for compatibility findings.

A finding fingerprint is used to identify the same logical
compatibility issue across scans.

The fingerprint intentionally does not include the source line
number because normal code movement should not make an existing
finding appear to be a completely new finding.
"""
from __future__ import annotations

import hashlib

from .finding import Finding


def _normalize_path(path: str) -> str:
    """Normalize file path to be portable across OS and scan invocation styles.

    Converts backslashes to forward slashes and makes the path relative
    by stripping any leading drive letter or absolute root, so that
    baselines remain valid when scanning with . vs absolute paths.
    """
    # Normalize separators
    p = path.replace("\\", "/")
    # Strip leading drive letter on Windows (C:/...)
    if len(p) >= 2 and p[1] == ":":
        p = p[2:]
    # Strip leading slashes to make relative
    p = p.lstrip("/")
    return p

def _normalize_path(path: str) -> str:
    """Normalize file path to be portable across OS and invocation styles."""
    p = path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        p = p[2:]
    return p.lstrip("/")

def finding_fingerprint(finding: Finding) -> str:
    """
    Return a stable fingerprint for a finding.

    The fingerprint identifies the logical finding rather than its
    exact source location.

    Included:
        - rule ID
        - runtime
        - affected version range
        - normalized file path
        - finding title

    Excluded:
        - line number
        - column number
        - description
        - suggestion
        - documentation URL

    Source locations are intentionally excluded so that moving code
    within a file does not automatically turn an existing finding
    into a new baseline finding.
    """
    payload = "\x1f".join(
        (
            finding.rule_id,
            finding.runtime.value,
            finding.affected_from,
            finding.affected_until,
            _normalize_path(finding.file),
            finding.title,
        )
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()