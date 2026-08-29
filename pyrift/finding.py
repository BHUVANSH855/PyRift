"""
pyrift.finding
~~~~~~~~~~~~~~
The Finding dataclass — every rule returns a list of these.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Confidence(str, Enum):
    """How certain pyrift is that this finding is a real issue."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceType(str, Enum):
    """What kind of evidence backs this rule."""

    OFFICIAL_DOCS = "official_docs"
    RUNTIME_PROBE = "runtime_probe"
    DEPRECATION_WARN = "deprecation_warn"
    PEP = "pep"
    OBSERVED = "observed"
    INFERRED = "inferred"


class Runtime(str, Enum):
    CPYTHON = "cpython"
    PYPY = "pypy"
    BOTH = "both"


_VERSION_RE = re.compile(
    r"^\s*(>=|<=|==|!=|>|<)?\s*(\d+\.\d+(?:\.\d+)?)\s*$"
)


def parse_version_range(spec: str) -> tuple[str, str]:
    """Parse a version expression into ``(from, until)`` strings.

    Supported forms::

        ">=3.13"           -> ("3.13", "")
        "<3.15"            -> ("", "3.15")
        ">=3.10,<3.14"     -> ("3.10", "3.14")
        ">=3.13, <3.16"    -> ("3.13", "3.16")
        ""                 -> ("", "")

    ``from`` is inclusive, ``until`` is exclusive.
    """
    if not spec or not spec.strip():
        return ("", "")

    from_ver = ""
    until_ver = ""

    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = _VERSION_RE.match(part)
        if m is None:
            continue
        op = m.group(1) or "=="
        ver = m.group(2)

        if op in (">=", ">"):
            from_ver = ver
        elif op in ("<=", "<"):
            until_ver = ver
        elif op == "==":
            from_ver = ver
            until_ver = ver
        elif op == "!=":
            pass  # excluded version — no range info

    return (from_ver, until_ver)


@dataclass
class Finding:
    """A single detected behaviour difference."""

    # Where
    file: str
    line: int
    col: int = 0

    # What
    rule_id: str = ""
    title: str = ""
    description: str = ""
    severity: Severity = Severity.WARNING

    # Confidence/evidence
    #
    # LOW/INFERRED are intentionally conservative defaults. A static
    # analyzer must not claim high confidence without documented evidence.
    confidence: Confidence = Confidence.LOW
    evidence_type: EvidenceType = EvidenceType.INFERRED
    evidence_source: str = ""

    # Which runtimes / versions are affected
    runtime: Runtime = Runtime.BOTH
    affected_from: str = ""
    affected_until: str = ""

    # Rule lifecycle (populated from rule_metadata)
    rule_status: str = ""
    rule_last_verified: str = ""

    # Fix guidance
    suggestion: str = ""
    docs_url: str = ""

    # Rule category (populated from BaseRule.category)
    category: str = "compatibility"

    def __post_init__(self) -> None:
        """Attach reviewed rule metadata when available."""
        try:
            from .rule_metadata import RULE_METADATA
        except ImportError:  # pragma: no cover
            return

        metadata = RULE_METADATA.get(self.rule_id)
        if metadata is None:  # pragma: no cover
            return

        self.confidence = metadata["confidence"]  # type: ignore[assignment]
        self.evidence_type = metadata["evidence_type"]  # type: ignore[assignment]
        self.evidence_source = metadata["evidence_source"]  # type: ignore[assignment]
        self.rule_status = str(metadata.get("status", ""))
        self.rule_last_verified = str(metadata.get("last_verified", ""))

        affected_versions = str(metadata.get("affected_versions", ""))
        if affected_versions and not self.affected_from and not self.affected_until:
            self.affected_from, self.affected_until = parse_version_range(
                affected_versions
            )

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}"
        if self.col:
            loc += f":{self.col}"

        sev = self.severity.value.upper()
        conf = self.confidence.value[0].upper()

        return (
            f"[{sev}/{conf}] {loc}  "
            f"{self.rule_id}: {self.title}"
        )

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "evidence_type": self.evidence_type.value,
            "evidence_source": self.evidence_source,
            "rule_status": self.rule_status,
            "rule_last_verified": self.rule_last_verified,
            "runtime": self.runtime.value,
            "affected_from": self.affected_from,
            "affected_until": self.affected_until,
            "suggestion": self.suggestion,
            "docs_url": self.docs_url,
            "category": self.category,
        }