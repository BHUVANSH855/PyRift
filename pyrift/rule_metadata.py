"""
pyrift.rule_metadata
~~~~~~~~~~~~~~~~~~~~

Authoritative confidence/evidence metadata for reviewed rules.

Rules without an entry intentionally remain at the conservative
Finding defaults:

    confidence = LOW
    evidence_type = INFERRED

This prevents unreviewed rules from silently claiming HIGH confidence.
"""

from __future__ import annotations

from .finding import Confidence, EvidenceType


def _metadata(
    confidence: str,
    evidence: str,
    *,
    status: str = "active",
    last_verified: str = "",
    affected_versions: str = "",
) -> dict[str, object]:
    if evidence.startswith("pep:"):
        evidence_type = EvidenceType.PEP
        evidence_source = evidence
    elif evidence == "official_docs":
        evidence_type = EvidenceType.OFFICIAL_DOCS
        evidence_source = evidence
    elif evidence == "runtime_probe":
        evidence_type = EvidenceType.RUNTIME_PROBE
        evidence_source = evidence
    elif evidence == "observed":
        evidence_type = EvidenceType.OBSERVED
        evidence_source = evidence
    elif evidence == "inferred":
        evidence_type = EvidenceType.INFERRED
        evidence_source = evidence
    elif evidence == "deprecation_warn":
        evidence_type = EvidenceType.DEPRECATION_WARN
        evidence_source = evidence
    else:
        raise ValueError(f"Unknown evidence type: {evidence}")

    return {
        "confidence": Confidence(confidence),
        "evidence_type": evidence_type,
        "evidence_source": evidence_source,
        "status": status,
        "last_verified": last_verified,
        "affected_versions": affected_versions,
    }


REQUIRED_METADATA_FIELDS = ("confidence", "evidence_type", "evidence_source", "status", "last_verified")


def validate_metadata() -> bool:
    """Return True if every RULE_METADATA entry has all required fields."""
    for entry in RULE_METADATA.values():
        for field in REQUIRED_METADATA_FIELDS:
            if field not in entry:
                return False
    return True


RULE_METADATA: dict[str, dict[str, object]] = {
    "CPY001": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY002": _metadata("high", "pep:678", last_verified="2026-08-29"),
    "CPY003": _metadata("high", "pep:604", last_verified="2026-08-29"),
    "CPY004": _metadata("high", "pep:680", last_verified="2026-08-29"),
    "CPY005": _metadata("high", "pep:634", last_verified="2026-08-29"),
    "CPY006": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY007": _metadata("high", "pep:594", last_verified="2026-08-29", affected_versions=">=3.13"),
    "CPY008": _metadata("medium", "official_docs", last_verified="2026-08-29"),
    "CPY009": _metadata("high", "pep:654", last_verified="2026-08-29"),
    "CPY010": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY011": _metadata("high", "pep:673", last_verified="2026-08-29"),
    "CPY012": _metadata("high", "pep:675", last_verified="2026-08-29"),
    "CPY013": _metadata("high", "pep:698", last_verified="2026-08-29"),
    "CPY014": _metadata("high", "pep:613", last_verified="2026-08-29"),
    "CPY015": _metadata("high", "pep:673", last_verified="2026-08-29"),
    "CPY016": _metadata("high", "pep:646", last_verified="2026-08-29"),
    "CPY017": _metadata("high", "pep:646", last_verified="2026-08-29"),
    "CPY018": _metadata("high", "pep:655", last_verified="2026-08-29"),
    "CPY019": _metadata("high", "pep:632", last_verified="2026-08-29"),
    "CPY020": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY021": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY022": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY023": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY024": _metadata("high", "pep:647", last_verified="2026-08-29"),
    "CPY025": _metadata("high", "pep:612", last_verified="2026-08-29"),
    "CPY026": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY027": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY028": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY029": _metadata("high", "pep:667", last_verified="2026-08-29"),
    "CPY030": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY031": _metadata("high", "pep:673", last_verified="2026-08-29"),
    "CPY032": _metadata("high", "pep:544", last_verified="2026-08-29"),
    "CPY033": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY034": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY035": _metadata("high", "pep:616", last_verified="2026-08-29"),
    "CPY036": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY037": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY038": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY039": _metadata("high", "pep:615", last_verified="2026-08-29"),
    "CPY040": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY041": _metadata("high", "pep:584", last_verified="2026-08-29"),
    "CPY042": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY043": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY044": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY045": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY046": _metadata("high", "pep:686", last_verified="2026-08-29", affected_versions="<=3.14"),
    "CPY047": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY048": _metadata("high", "pep:734", last_verified="2026-08-29"),
    "CPY049": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY050": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY051": _metadata("medium", "pep:703", last_verified="2026-08-29"),
    "CPY053": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "CPY054": _metadata("high", "official_docs", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY055": _metadata("high", "official_docs", last_verified="2026-08-29", affected_versions=">=3.14"),
    "CPY057": _metadata("high", "runtime_probe", last_verified="2026-08-29"),
    "CPY062": _metadata("high", "pep:750", last_verified="2026-08-29"),
    "CPY063": _metadata("high", "pep:749", last_verified="2026-08-29"),
    "PPY001": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY002": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY003": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY004": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY005": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY006": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY007": _metadata("low", "observed", last_verified="2026-08-29"),
    "PPY008": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY009": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY010": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY011": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY012": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY013": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY014": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY015": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY016": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY017": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY018": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY019": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY021": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY022": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY023": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY024": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY025": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY026": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY027": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY028": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY029": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY030": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY031": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY032": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY033": _metadata("medium", "inferred", last_verified="2026-08-29"),
    "PPY034": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY035": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY036": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY037": _metadata("low", "observed", last_verified="2026-08-29"),
    "PPY038": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY039": _metadata("low", "observed", last_verified="2026-08-29"),
    "PPY040": _metadata("low", "observed", last_verified="2026-08-29"),
    "PPY041": _metadata("high", "pep:584", last_verified="2026-08-29"),
    "PPY042": _metadata("low", "observed", last_verified="2026-08-29"),
    "PPY044": _metadata("medium", "inferred", last_verified="2026-08-29"),
    "PPY045": _metadata("high", "official_docs", last_verified="2026-08-29"),
    "PPY047": _metadata("high", "official_docs", last_verified="2026-08-29"),
}