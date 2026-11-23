"""Tests for CPY081 -- sys.last_type/last_value/last_traceback deprecated 3.12."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy081_sys_last_exc import SysLastExcRule

RULE = SysLastExcRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_sys_last_type():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY081"


def test_sys_last_value():
    src = "import sys\nprint(sys.last_value)"
    assert len(_findings(src)) == 1


def test_sys_last_traceback():
    src = "import sys\nprint(sys.last_traceback)"
    assert len(_findings(src)) == 1


def test_all_three_deprecated():
    src = (
        "import sys\n"
        "t = sys.last_type\n"
        "v = sys.last_value\n"
        "tb = sys.last_traceback\n"
    )
    assert len(_findings(src)) == 3


def test_nested_attribute_access():
    src = "import sys\nif sys.last_type is not None: pass"
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_sys_last_exc_ok():
    src = "import sys\nprint(sys.last_exc)"
    assert _findings(src) == []


def test_sys_version_ok():
    src = "import sys\nprint(sys.version)"
    assert _findings(src) == []


def test_unrelated_last_attr():
    src = "obj.last_type = None"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []