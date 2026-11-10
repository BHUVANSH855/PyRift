"""Tombstone smoke test for PPY020.

PPY020 was retired (kwargs string-key assumption rule — removed because the
detection was unreliable).  This test asserts that the slot is permanently
reserved: the rule ID must not appear in ALL_RULES, and the RULE_METADATA
tombstone entry must be present.
"""

from pyrift.rule_metadata import RULE_METADATA
from pyrift.scanner import ALL_RULES


def test_ppy020_not_in_all_rules():
    """PPY020 must be absent from the active rule set."""
    active_ids = {rule.rule_id for rule in ALL_RULES}
    assert "PPY020" not in active_ids, (
        "PPY020 is a retired rule slot and must never be re-used as a live rule."
    )


def test_ppy020_tombstone_in_metadata():
    """PPY020 must have a tombstone entry in RULE_METADATA."""
    assert "PPY020" in RULE_METADATA, (
        "PPY020 tombstone entry is missing from RULE_METADATA; "
        "retired IDs must be permanently reserved."
    )
    assert RULE_METADATA["PPY020"].get("status") == "tombstone", (
        "PPY020 must have status='tombstone' in RULE_METADATA."
    )
