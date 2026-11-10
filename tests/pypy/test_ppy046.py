"""Tombstone smoke test for PPY046.

PPY046 was retired (debug constant rule — removed because it produced too
many false positives in legitimate debug builds).  This test asserts that
the slot is permanently reserved: the rule ID must not appear in ALL_RULES,
and the RULE_METADATA tombstone entry must be present.
"""

from pyrift.rule_metadata import RULE_METADATA
from pyrift.scanner import ALL_RULES


def test_ppy046_not_in_all_rules():
    """PPY046 must be absent from the active rule set."""
    active_ids = {rule.rule_id for rule in ALL_RULES}
    assert "PPY046" not in active_ids, (
        "PPY046 is a retired rule slot and must never be re-used as a live rule."
    )


def test_ppy046_tombstone_in_metadata():
    """PPY046 must have a tombstone entry in RULE_METADATA."""
    assert "PPY046" in RULE_METADATA, (
        "PPY046 tombstone entry is missing from RULE_METADATA; "
        "retired IDs must be permanently reserved."
    )
    assert RULE_METADATA["PPY046"].get("status") == "tombstone", (
        "PPY046 must have status='tombstone' in RULE_METADATA."
    )
