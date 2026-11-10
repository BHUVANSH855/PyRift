"""PPY048 was deleted — it contradicted PPY013.

sys.getsizeof() raises TypeError on PyPy, so a rule claiming it
'returns different values' was incorrect.  This file is kept only for
history; the test_rule_inventory.py known_removed set references it.
"""
import importlib

from pyrift.scanner import ALL_RULES


def test_ppy048_is_removed():
    """PPY048 should not be importable as a live rule."""
    mod = importlib.import_module("pyrift.rules.pypy.ppy048_sys_getsizeof")
    assert not hasattr(mod, "SysGetsizeofRule"), (
        "PPY048 SysGetsizeofRule should be removed"
    )


def test_ppy048_not_in_all_rules():
    """PPY048 must not appear in the active scanner rule set."""
    active_ids = {rule.rule_id for rule in ALL_RULES}
    assert "PPY048" not in active_ids, (
        "PPY048 is a deleted rule and must not appear in ALL_RULES."
    )


def test_ppy048_module_is_importable():
    """The stub module must be importable without errors (graceful removal)."""
    mod = importlib.import_module("pyrift.rules.pypy.ppy048_sys_getsizeof")
    assert mod is not None
