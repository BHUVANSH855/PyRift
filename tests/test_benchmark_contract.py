import json
from pathlib import Path

from pyrift.finding import Confidence, EvidenceType, Finding


def test_expected_json_has_valid_rule_contracts():
    path = (
        Path(__file__).parent.parent
        / "benchmark"
        / "expected.json"
    )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    rules = data["rules"]

    assert rules

    for rule_id, contract in rules.items():
        assert rule_id.startswith(("CPY", "PPY"))
        assert contract["min_true_positives"] >= 0
        assert contract["max_false_positives"] >= 0
        assert contract["confidence"] in {
            "high",
            "medium",
            "low",
        }
        assert contract["evidence"]


def test_reviewed_metadata_is_available_to_findings():
    finding = Finding(
        file="example.py",
        line=1,
        rule_id="CPY051",
    )

    assert finding.confidence == Confidence.MEDIUM
    assert finding.evidence_type == EvidenceType.PEP
    assert finding.evidence_source == "pep:703"