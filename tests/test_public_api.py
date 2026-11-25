"""Tests for pyrift's public package API."""

import pyrift


def test_confidence_is_public():
    from pyrift import Confidence

    assert Confidence is pyrift.Confidence


def test_evidence_type_is_public():
    from pyrift import EvidenceType

    assert EvidenceType is pyrift.EvidenceType


def test_intent_basis_is_public():
    from pyrift import IntentBasis

    assert IntentBasis is pyrift.IntentBasis


def test_public_metadata_enums_are_in_all():
    assert "Confidence" in pyrift.__all__
    assert "EvidenceType" in pyrift.__all__
    assert "IntentBasis" in pyrift.__all__




def test_base_rule_is_public():
    from pyrift import BaseRule

    assert BaseRule is pyrift.BaseRule


def test_severity_is_public():
    from pyrift import Severity

    assert Severity is pyrift.Severity


def test_plugin_api_in_all():
    assert "BaseRule" in pyrift.__all__
    assert "Severity" in pyrift.__all__
