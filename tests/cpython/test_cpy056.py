"""Tombstone smoke test for CPY056.

CPY056 was a draft rule that was never shipped — the slot was reserved
before any implementation reached the codebase.  This test asserts that
the slot is permanently reserved: the rule ID must not appear in ALL_RULES,
and the RULE_METADATA tombstone entry must be present.
"""

from pyrift.rule_metadata import RULE_METADATA
from pyrift.scanner import ALL_RULES


def test_cpy056_not_in_all_rules():
    """CPY056 must be absent from the active rule set."""
    active_ids = {rule.rule_id for rule in ALL_RULES}
    assert "CPY056" not in active_ids, (
        "CPY056 is a reserved draft slot and must never be used as a live rule."
    )


def test_cpy056_tombstone_in_metadata():
    """CPY056 must have a tombstone entry in RULE_METADATA."""
    assert "CPY056" in RULE_METADATA, (
        "CPY056 tombstone entry is missing from RULE_METADATA; "
        "retired IDs must be permanently reserved."
    )
    assert RULE_METADATA["CPY056"].get("status") == "tombstone", (
        "CPY056 must have status='tombstone' in RULE_METADATA."
    )
