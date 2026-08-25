"""
pyrift.baseline
~~~~~~~~~~~~~~~
Persistent baseline support for compatibility findings.
"""
from __future__ import annotations

import json
from pathlib import Path

from .finding import Finding
from .fingerprint import finding_fingerprint

BASELINE_VERSION = 1
DEFAULT_BASELINE_FILE = ".pyrift-baseline.json"


class BaselineError(ValueError):
    """Raised when a pyrift baseline is invalid."""


def create_baseline(
    findings: list[Finding],
    path: str | Path,
) -> None:
    """
    Write the fingerprints of findings to a baseline file.

    The output is deterministic so the baseline can be committed
    cleanly and reviewed in version control.
    """
    baseline_path = Path(path)

    fingerprints = sorted(
        {
            finding_fingerprint(finding)
            for finding in findings
        }
    )

    data = {
        "version": BASELINE_VERSION,
        "findings": fingerprints,
    }

    baseline_path.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def load_baseline(path: str | Path) -> set[str]:
    """
    Load finding fingerprints from a baseline file.

    Missing baseline files return an empty set.

    Invalid baseline files raise BaselineError instead of silently
    ignoring malformed data.
    """
    baseline_path = Path(path)

    if not baseline_path.exists():
        return set()

    try:
        data = json.loads(
            baseline_path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BaselineError(
            f"Unable to read baseline file: {baseline_path}"
        ) from exc

    if not isinstance(data, dict):
        raise BaselineError(
            "Baseline must contain a JSON object."
        )

    version = data.get("version")

    if version != BASELINE_VERSION:
        raise BaselineError(
            f"Unsupported baseline version: {version!r}"
        )

    fingerprints = data.get("findings")

    if not isinstance(fingerprints, list):
        raise BaselineError(
            "Baseline 'findings' must be a list."
        )

    if not all(
        isinstance(fingerprint, str)
        for fingerprint in fingerprints
    ):
        raise BaselineError(
            "Baseline findings must contain strings."
        )

    return set(fingerprints)


def filter_baseline_findings(
    findings: list[Finding],
    baseline: set[str],
) -> tuple[list[Finding], list[Finding]]:
    """
    Split findings into baseline and new findings.

    Returns:

        (new_findings, baseline_findings)
    """
    new_findings: list[Finding] = []
    baseline_findings: list[Finding] = []

    for finding in findings:
        fingerprint = finding_fingerprint(finding)

        if fingerprint in baseline:
            baseline_findings.append(finding)
        else:
            new_findings.append(finding)

    return new_findings, baseline_findings