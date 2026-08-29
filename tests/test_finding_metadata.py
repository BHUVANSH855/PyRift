from pyrift.finding import (
    Confidence,
    EvidenceType,
    Finding,
    IntentBasis,
    Runtime,
)


def test_reviewed_rule_gets_authoritative_metadata():
    finding = Finding(
        file="example.py",
        line=1,
        rule_id="CPY051",
        runtime=Runtime.CPYTHON,
    )

    assert finding.confidence == Confidence.MEDIUM
    assert finding.evidence_type == EvidenceType.PEP
    assert finding.evidence_source == "pep:703"
    assert finding.intent_basis == IntentBasis.DOCUMENTED


def test_unreviewed_rule_uses_conservative_defaults():
    finding = Finding(
        file="example.py",
        line=1,
        rule_id="UNREVIEWED",
    )

    assert finding.confidence == Confidence.LOW
    assert finding.evidence_type == EvidenceType.INFERRED
    assert finding.evidence_source == ""
    assert finding.intent_basis == IntentBasis.INFERRED


def test_evidence_is_serialized():
    finding = Finding(
        file="example.py",
        line=1,
        rule_id="CPY051",
    )

    data = finding.to_dict()

    assert data["confidence"] == "medium"
    assert data["evidence_type"] == "pep"
    assert data["evidence_source"] == "pep:703"
    assert data["intent_basis"] == "documented"