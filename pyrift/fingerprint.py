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
            finding.file.replace("\\", "/"),
            finding.title,
        )
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()