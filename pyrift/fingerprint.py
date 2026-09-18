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


def _normalize_path(path: str, root: str = "") -> str:
    """Normalize file path to be portable across OS and scan invocation styles.

    Converts backslashes to forward slashes and makes the path relative
    by stripping any leading drive letter or absolute root, so that
    baselines remain valid when scanning with . vs absolute paths.

    If *root* is provided, the path is made relative to it so that
    absolute and relative scans of the same file produce the same
    normalized path.
    """
    # Normalize separators
    p = path.replace("\\", "/")
    root_normalized = root.replace("\\", "/") if root else ""

    if root_normalized:
        # Make path relative to root
        root_normalized = root_normalized.rstrip("/") + "/"
        if p.startswith(root_normalized):
            p = p[len(root_normalized):]
        elif p == root_normalized.rstrip("/"):
            p = ""
    else:
        # Strip leading drive letter on Windows (C:/...)
        if len(p) >= 2 and p[1] == ":":
            p = p[2:]
        # Strip leading slashes to make relative
        p = p.lstrip("/")

    # Strip leading ./ so that ./src/file.py and src/file.py normalize
    # to the same value regardless of how the scan was invoked.
    while p.startswith("./"):
        p = p[2:]

    return p

def _base_key(finding: Finding, root: str = "") -> str:
    """The part of a finding's identity that does *not* disambiguate
    multiple occurrences of the same logical finding within one file."""
    return "\x1f".join(
        (
            finding.rule_id,
            finding.runtime.value,
            finding.affected_from,
            finding.affected_until,
            _normalize_path(finding.file, root),
            finding.title,
        )
    )


def finding_fingerprint(finding: Finding, root: str = "") -> str:
    """
    Return a stable fingerprint for a *single* finding, in isolation.

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

    Known limitation (P0 audit #6/#140): called on a single finding in
    isolation, this cannot distinguish multiple identical occurrences of
    the same rule/title in the same file (e.g. two independent calls to
    the same deprecated API) -- they hash identically. For a full scan
    result where that distinction matters (baseline creation/filtering),
    use :func:`compute_fingerprints` instead, which disambiguates
    repeated occurrences by their order within the file.
    """
    payload = "\x1f".join((_base_key(finding, root), "0"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_fingerprints(findings: list[Finding], root: str = "") -> list[str]:
    """
    Return a stable fingerprint for each finding in *findings*, aligned
    by index, disambiguating multiple identical occurrences of the same
    logical finding within a file (P0 fix, 2026-09 audit #6/#140).

    Without this, two independent uses of the same deprecated API in one
    file -- same rule, same runtime, same affected range, same title --
    collapse to the *same* fingerprint, so a baseline can't tell "2 known
    occurrences" from "1 known occurrence", and can silently swallow a
    second, genuinely new occurrence as already-baselined.

    Disambiguation is based on each finding's rank by distinct
    ``(line, col)`` position among other findings sharing the same base
    identity, not on list input order -- so the same source file
    produces the same set of fingerprints regardless of what order
    findings happen to be passed in, keeping baseline creation and later
    filtering consistent. Genuinely identical entries (same rule, same
    exact source position) still collapse to a single fingerprint, as
    before; only entries that differ in position get distinct ones.

    This still does not survive *reordering* the duplicate call sites
    within the file (occurrence 1 and occurrence 2 could swap identities
    if their relative line order changes) -- but since the two findings
    are, by construction, otherwise indistinguishable (same rule, same
    title, same range), swapping which fingerprint refers to which is
    harmless for baseline purposes: the count of known occurrences is
    preserved either way. What this fixes is the count collapsing to 1.
    """
    base_keys = [_base_key(finding, root) for finding in findings]

    groups: dict[str, list[int]] = {}
    for idx, key in enumerate(base_keys):
        groups.setdefault(key, []).append(idx)

    occurrence_index = [0] * len(findings)
    for indices in groups.values():
        # Rank by *distinct* (line, col) positions, not by raw index:
        # this keeps truly identical entries (same rule, same exact
        # source position -- e.g. the same Finding object/data passed
        # twice) collapsing to one fingerprint as before, while entries
        # that differ in position (the actual collision this fixes) get
        # distinct fingerprints.
        distinct_positions = sorted(
            {(findings[i].line, findings[i].col) for i in indices}
        )
        position_rank = {
            position: rank for rank, position in enumerate(distinct_positions)
        }
        for i in indices:
            occurrence_index[i] = position_rank[(findings[i].line, findings[i].col)]

    fingerprints = []
    for idx in range(len(findings)):
        payload = "\x1f".join((base_keys[idx], str(occurrence_index[idx])))
        fingerprints.append(hashlib.sha256(payload.encode("utf-8")).hexdigest())

    return fingerprints