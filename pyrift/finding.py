"""
pyrift.finding
~~~~~~~~~~~~~~
The Finding dataclass — every rule returns a list of these.
"""
from __future__ import annotations

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

    # Fix guidance
    suggestion: str = ""
    docs_url: str = ""

    def __post_init__(self) -> None:
        """Attach reviewed rule metadata when available."""
        try:
            from .rule_metadata import RULE_METADATA
        except ImportError:
            return

        metadata = RULE_METADATA.get(self.rule_id)
        if metadata is None:
            return

        self.confidence = metadata["confidence"]  # type: ignore[assignment]
        self.evidence_type = metadata["evidence_type"]  # type: ignore[assignment]
        self.evidence_source = metadata["evidence_source"]  # type: ignore[assignment]

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
            "runtime": self.runtime.value,
            "affected_from": self.affected_from,
            "affected_until": self.affected_until,
            "suggestion": self.suggestion,
            "docs_url": self.docs_url,
        }