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
    }


RULE_METADATA: dict[str, dict[str, object]] = {
    "CPY001": _metadata("high", "official_docs"),
    "CPY002": _metadata("high", "pep:678"),
    "CPY003": _metadata("high", "pep:604"),
    "CPY004": _metadata("high", "pep:680"),
    "CPY005": _metadata("high", "pep:634"),
    "CPY006": _metadata("high", "official_docs"),
    "CPY007": _metadata("high", "pep:594"),
    "CPY008": _metadata("medium", "official_docs"),
    "CPY009": _metadata("high", "pep:654"),
    "CPY010": _metadata("high", "official_docs"),
    "CPY011": _metadata("high", "pep:673"),
    "CPY012": _metadata("high", "pep:675"),
    "CPY013": _metadata("high", "pep:698"),
    "CPY014": _metadata("high", "pep:613"),
    "CPY015": _metadata("high", "pep:673"),
    "CPY016": _metadata("high", "pep:646"),
    "CPY017": _metadata("high", "pep:646"),
    "CPY018": _metadata("high", "pep:655"),
    "CPY019": _metadata("high", "pep:632"),
    "CPY020": _metadata("high", "official_docs"),
    "CPY022": _metadata("high", "runtime_probe"),
    "CPY023": _metadata("high", "runtime_probe"),
    "CPY026": _metadata("high", "official_docs"),
    "CPY028": _metadata("high", "official_docs"),
    "CPY029": _metadata("high", "pep:667"),
    "CPY036": _metadata("high", "runtime_probe"),
    "CPY037": _metadata("high", "runtime_probe"),
    "CPY038": _metadata("high", "runtime_probe"),
    "CPY041": _metadata("high", "pep:584"),
    "CPY046": _metadata("high", "pep:686"),
    "CPY047": _metadata("high", "official_docs"),
    "CPY048": _metadata("high", "pep:734"),
    "CPY049": _metadata("high", "official_docs"),
    "CPY050": _metadata("high", "runtime_probe"),
    "CPY051": _metadata("medium", "pep:703"),
    "CPY054": _metadata("high", "official_docs"),
    "CPY055": _metadata("high", "official_docs"),
    "CPY057": _metadata("high", "runtime_probe"),
    "CPY062": _metadata("high", "pep:750"),
    "CPY063": _metadata("high", "pep:749"),
    "PPY001": _metadata("high", "official_docs"),
    "PPY002": _metadata("high", "official_docs"),
    "PPY003": _metadata("high", "official_docs"),
    "PPY004": _metadata("high", "official_docs"),
    "PPY007": _metadata("low", "observed"),
    "PPY008": _metadata("high", "official_docs"),
    "PPY013": _metadata("high", "official_docs"),
    "PPY014": _metadata("high", "official_docs"),
    "PPY016": _metadata("high", "official_docs"),
    "PPY019": _metadata("high", "official_docs"),
    "PPY022": _metadata("high", "official_docs"),
    "PPY030": _metadata("high", "official_docs"),
    "PPY031": _metadata("high", "official_docs"),
    "PPY033": _metadata("medium", "inferred"),
    "PPY034": _metadata("high", "official_docs"),
    "PPY035": _metadata("high", "official_docs"),
    "PPY037": _metadata("low", "observed"),
    "PPY038": _metadata("high", "official_docs"),
    "PPY039": _metadata("low", "observed"),
    "PPY040": _metadata("low", "observed"),
    "PPY042": _metadata("low", "observed"),
    "PPY044": _metadata("medium", "inferred"),
    "PPY045": _metadata("high", "official_docs"),
    "PPY046": _metadata("low", "observed"),
    "PPY047": _metadata("high", "official_docs"),
}