"""
pyrift.finding
~~~~~~~~~~~~~~
The Finding dataclass — every rule returns a list of these.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR   = "error"    # silent wrong behaviour — data corruption, crash
    WARNING = "warning"  # different behaviour — may or may not matter
    INFO    = "info"     # informational — worth knowing


class Confidence(str, Enum):
    """How certain pyrift is that this finding is a real issue.

    HIGH   — backed by official docs or confirmed runtime differential
    MEDIUM — strongly implied by docs/behaviour but not formally verified
    LOW    — observed in practice or inferred; not formally documented
    """
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"


class EvidenceType(str, Enum):
    """What kind of evidence backs this rule."""
    OFFICIAL_DOCS    = "official_docs"     # explicitly stated in Python/PyPy docs
    RUNTIME_PROBE    = "runtime_probe"     # confirmed by running code on both runtimes
    DEPRECATION_WARN = "deprecation_warn"  # Python emits DeprecationWarning
    PEP              = "pep"               # specified in a Python Enhancement Proposal
    OBSERVED         = "observed"          # observed in practice, not formally documented
    INFERRED         = "inferred"          # logically implied but not directly observed


class Runtime(str, Enum):
    CPYTHON = "cpython"
    PYPY    = "pypy"
    BOTH    = "both"


@dataclass
class Finding:
    """A single detected behaviour difference."""

    # Where
    file:    str
    line:    int
    col:     int = 0

    # What
    rule_id:     str = ""
    title:       str = ""
    description: str = ""
    severity:    Severity = Severity.WARNING

    # Confidence — independent of severity
    # HIGH = backed by official docs or runtime proof
    # MEDIUM = strongly implied
    # LOW = observed/inferred
    confidence: Confidence = Confidence.HIGH

    # Which runtimes / versions are affected
    runtime:         Runtime = Runtime.BOTH
    affected_from:   str = ""
    affected_until:  str = ""

    # Fix guidance
    suggestion: str = ""
    docs_url:   str = ""

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}"
        if self.col:
            loc += f":{self.col}"
        sev = self.severity.value.upper()
        conf = self.confidence.value[0].upper()  # H/M/L
        return f"[{sev}/{conf}] {loc}  {self.rule_id}: {self.title}"

    def to_dict(self) -> dict:
        return {
            "file":           self.file,
            "line":           self.line,
            "col":            self.col,
            "rule_id":        self.rule_id,
            "title":          self.title,
            "description":    self.description,
            "severity":       self.severity.value,
            "confidence":     self.confidence.value,
            "runtime":        self.runtime.value,
            "affected_from":  self.affected_from,
            "affected_until": self.affected_until,
            "suggestion":     self.suggestion,
            "docs_url":       self.docs_url,
        }