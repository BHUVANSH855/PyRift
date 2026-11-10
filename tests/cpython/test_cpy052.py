"""Tombstone smoke test for CPY052.

CPY052 was retired (wrong detector — superseded by CPY051).  This test
asserts that the slot is permanently reserved: the rule ID must not appear
in ALL_RULES, and the RULE_METADATA tombstone entry must be present so that
a user's ``--ignore CPY052`` suppression is never silently re-applied to a
different rule in a future release.
"""

from pyrift.rule_metadata import RULE_METADATA
from pyrift.scanner import ALL_RULES


def test_cpy052_not_in_all_rules():
    """CPY052 must be absent from the active rule set."""
    active_ids = {rule.rule_id for rule in ALL_RULES}
    assert "CPY052" not in active_ids, (
        "CPY052 is a retired rule slot and must never be re-used as a live rule."
    )


def test_cpy052_tombstone_in_metadata():
    """CPY052 must have a tombstone entry in RULE_METADATA."""
    assert "CPY052" in RULE_METADATA, (
        "CPY052 tombstone entry is missing from RULE_METADATA; "
        "retired IDs must be permanently reserved."
    )
    assert RULE_METADATA["CPY052"].get("status") == "tombstone", (
        "CPY052 must have status='tombstone' in RULE_METADATA."
    )
