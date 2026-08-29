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