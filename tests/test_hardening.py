"""
Tests for hardening Phases 2, 8, and 9.

Phase 2: Version metadata is authoritative in Finding.
Phase 8: Rule evidence contract validation.
Phase 9: Rule lifecycle validation (uniqueness, tombstones, bidirectional).
"""
from __future__ import annotations

from pathlib import Path

from pyrift.finding import Finding, parse_version_range
from pyrift.rule_metadata import (
    REQUIRED_METADATA_FIELDS,
    RULE_METADATA,
    validate_metadata,
)
from pyrift.scanner import ALL_RULES

ROOT = Path(__file__).resolve().parents[1]

REMOVED_IDS = {"CPY052", "PPY020", "PPY046"}

TOMBSTONE_FILES = {
    "CPY052": ROOT / "pyrift" / "rules" / "cpython" / "cpy052_free_threaded_threading_local.py",
    "PPY020": ROOT / "pyrift" / "rules" / "pypy" / "ppy020_kwargs_string_keys.py",
    "PPY046": ROOT / "pyrift" / "rules" / "pypy" / "ppy046_debug_constant.py",
}


# ---------------------------------------------------------------------------
# Phase 2 — parse_version_range
# ---------------------------------------------------------------------------

class TestParseVersionRange:
    def test_empty_string(self):
        assert parse_version_range("") == ("", "")

    def test_whitespace_only(self):
        assert parse_version_range("   ") == ("", "")

    def test_gte(self):
        assert parse_version_range(">=3.13") == ("3.13", "")

    def test_gt(self):
        assert parse_version_range(">3.10") == ("3.10", "")

    def test_lt(self):
        assert parse_version_range("<3.15") == ("", "3.15")

    def test_lte(self):
        assert parse_version_range("<=3.14") == ("", "3.14")

    def test_range_comma(self):
        assert parse_version_range(">=3.10,<3.14") == ("3.10", "3.14")

    def test_range_comma_with_space(self):
        assert parse_version_range(">=3.13, <3.16") == ("3.13", "3.16")

    def test_three_part_version(self):
        assert parse_version_range(">=3.13.1") == ("3.13.1", "")

    def test_eq(self):
        assert parse_version_range("==3.12") == ("3.12", "3.12")

    def test_neq_ignored(self):
        assert parse_version_range("!=3.11") == ("", "")


# ---------------------------------------------------------------------------
# Phase 2 — affected_versions propagation
# ---------------------------------------------------------------------------

class TestAffectedVersions:
    def test_cpy007_has_affected_from(self):
        finding = Finding(file="x.py", line=1, rule_id="CPY007")
        assert finding.affected_from == "3.13"
        assert finding.affected_until == ""

    def test_cpy046_has_affected_until(self):
        finding = Finding(file="x.py", line=1, rule_id="CPY046")
        assert finding.affected_from == ""
        assert finding.affected_until == "3.14"

    def test_cpy054_has_affected_from(self):
        finding = Finding(file="x.py", line=1, rule_id="CPY054")
        assert finding.affected_from == "3.14"
        assert finding.affected_until == ""

    def test_unmapped_rule_no_version(self):
        finding = Finding(file="x.py", line=1, rule_id="CPY999")
        assert finding.affected_from == ""
        assert finding.affected_until == ""

    def test_pre_filled_values_not_overwritten(self):
        finding = Finding(
            file="x.py",
            line=1,
            rule_id="CPY007",
            affected_from="3.12",
            affected_until="4.0",
        )
        assert finding.affected_from == "3.12"
        assert finding.affected_until == "4.0"

    def test_affected_versions_in_to_dict(self):
        finding = Finding(file="x.py", line=1, rule_id="CPY007")
        data = finding.to_dict()
        assert data["affected_from"] == "3.13"
        assert data["affected_until"] == ""


# ---------------------------------------------------------------------------
# Phase 8 — validate_metadata
# ---------------------------------------------------------------------------

class TestValidateMetadata:
    def test_validate_returns_true(self):
        assert validate_metadata() is True

    def test_required_fields_constant(self):
        assert "confidence" in REQUIRED_METADATA_FIELDS
        assert "evidence_type" in REQUIRED_METADATA_FIELDS
        assert "evidence_source" in REQUIRED_METADATA_FIELDS
        assert "intent_basis" in REQUIRED_METADATA_FIELDS
        assert "status" in REQUIRED_METADATA_FIELDS
        assert "last_verified" in REQUIRED_METADATA_FIELDS

    def test_all_entries_have_required_fields(self):
        for rule_id, entry in RULE_METADATA.items():
            for field in REQUIRED_METADATA_FIELDS:
                assert field in entry, f"{rule_id} missing {field}"


# ---------------------------------------------------------------------------
# Phase 9 — Rule lifecycle validation
# ---------------------------------------------------------------------------

class TestRuleLifecycle:
    def test_active_rule_ids_are_unique(self):
        ids = [rule.rule_id for rule in ALL_RULES]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs in ALL_RULES"

    def test_no_active_rule_overlaps_removed(self):
        active_ids = {rule.rule_id for rule in ALL_RULES}
        overlap = active_ids & REMOVED_IDS
        assert not overlap, f"Active rules overlap with removed: {overlap}"

    def test_every_imported_rule_has_metadata(self):
        active_ids = {rule.rule_id for rule in ALL_RULES}
        missing = active_ids - set(RULE_METADATA)
        assert not missing, f"Rules without metadata: {sorted(missing)}"

    def test_every_metadata_entry_has_imported_rule(self):
        active_ids = {rule.rule_id for rule in ALL_RULES}
        orphaned = set(RULE_METADATA) - active_ids
        assert not orphaned, f"Orphaned metadata entries: {sorted(orphaned)}"

    def test_tombstone_files_exist(self):
        for rule_id, path in TOMBSTONE_FILES.items():
            assert path.exists(), f"Tombstone file missing for {rule_id}: {path}"

    def test_tombstone_files_are_not_imported(self):
        active_ids = {rule.rule_id for rule in ALL_RULES}
        for removed_id in REMOVED_IDS:
            assert removed_id not in active_ids
