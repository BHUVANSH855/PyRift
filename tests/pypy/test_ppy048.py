"""PPY048 was deleted — it contradicted PPY013.

sys.getsizeof() raises TypeError on PyPy, so a rule claiming it
'returns different values' was incorrect.  This file is kept only for
history; the test_rule_inventory.py known_removed set references it.
"""


def test_ppy048_is_removed():
    """PPY048 should not be importable as a live rule."""
    import importlib
    mod = importlib.import_module("pyrift.rules.pypy.ppy048_sys_getsizeof")
    assert not hasattr(mod, "SysGetsizeofRule"), (
        "PPY048 SysGetsizeofRule should be removed"
    )
