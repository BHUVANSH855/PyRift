"""Tombstone smoke test for PPY043.

PPY043 (__slots__ memory savings differ on PyPy) was removed because
detection was unreliable across PyPy versions.  Historical scan snapshots
in compatibility-benchmark/ still reference this ID; this test ensures
the slot is permanently reserved so those references remain meaningful.
"""

from pyrift.rule_metadata import RULE_METADATA
from pyrift.scanner import ALL_RULES


def test_ppy043_not_in_all_rules():
    """PPY043 must be absent from the active rule set."""
    active_ids = {rule.rule_id for rule in ALL_RULES}
    assert "PPY043" not in active_ids, (
        "PPY043 is a retired rule slot and must never be re-used as a live rule."
    )


def test_ppy043_tombstone_in_metadata():
    """PPY043 must have a tombstone entry in RULE_METADATA."""
    assert "PPY043" in RULE_METADATA, (
        "PPY043 tombstone entry is missing from RULE_METADATA; "
        "retired IDs must be permanently reserved."
    )
    assert RULE_METADATA["PPY043"].get("status") == "tombstone", (
        "PPY043 must have status='tombstone' in RULE_METADATA."
    )
