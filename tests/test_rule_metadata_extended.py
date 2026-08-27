"""Extended tests for rule_metadata — coverage of edge cases."""
from __future__ import annotations

import pytest

from pyrift.finding import Confidence, EvidenceType
from pyrift.rule_metadata import RULE_METADATA, _metadata


class TestMetadataFunction:
    def test_pep_evidence(self):
        m = _metadata("high", "pep:584")
        assert m["confidence"] == Confidence.HIGH
        assert m["evidence_type"] == EvidenceType.PEP
        assert m["evidence_source"] == "pep:584"

    def test_official_docs_evidence(self):
        m = _metadata("high", "official_docs")
        assert m["evidence_type"] == EvidenceType.OFFICIAL_DOCS

    def test_runtime_probe_evidence(self):
        m = _metadata("high", "runtime_probe")
        assert m["evidence_type"] == EvidenceType.RUNTIME_PROBE

    def test_observed_evidence(self):
        m = _metadata("low", "observed")
        assert m["evidence_type"] == EvidenceType.OBSERVED
        assert m["confidence"] == Confidence.LOW

    def test_inferred_evidence(self):
        m = _metadata("medium", "inferred")
        assert m["evidence_type"] == EvidenceType.INFERRED
        assert m["confidence"] == Confidence.MEDIUM

    def test_deprecation_warn_evidence(self):
        m = _metadata("high", "deprecation_warn")
        assert m["evidence_type"] == EvidenceType.DEPRECATION_WARN

    def test_unknown_evidence_raises(self):
        with pytest.raises(ValueError, match="Unknown evidence type"):
            _metadata("high", "unknown_type_xyz")

    def test_low_confidence(self):
        m = _metadata("low", "observed")
        assert m["confidence"] == Confidence.LOW

    def test_medium_confidence(self):
        m = _metadata("medium", "inferred")
        assert m["confidence"] == Confidence.MEDIUM


class TestRuleMetadataRegistry:
    def test_all_rules_have_metadata(self):
        """Every rule in RULE_METADATA has valid confidence and evidence."""
        from pyrift import ALL_RULES
        rule_ids = {r.rule_id for r in ALL_RULES}
        for rule_id in rule_ids:
            if rule_id in RULE_METADATA:
                m = RULE_METADATA[rule_id]
                assert isinstance(m["confidence"], Confidence)
                assert isinstance(m["evidence_type"], EvidenceType)

    def test_cpy001_is_high_confidence(self):
        assert RULE_METADATA["CPY001"]["confidence"] == Confidence.HIGH

    def test_ppy007_is_low_confidence(self):
        # PPY007 is observed, not formally documented
        assert RULE_METADATA["PPY007"]["confidence"] == Confidence.LOW

    def test_no_unknown_rule_ids(self):
        """RULE_METADATA should only contain real rule IDs."""
        from pyrift import ALL_RULES
        all_ids = {r.rule_id for r in ALL_RULES}
        for rule_id in RULE_METADATA:
            assert rule_id in all_ids, f"{rule_id} in metadata but not in ALL_RULES"