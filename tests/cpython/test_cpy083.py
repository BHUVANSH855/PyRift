"""Tests for CPY083 -- array.array('u', ...) deprecated 3.13, removed 3.16."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy083_array_u_typecode import ArrayUTypecodeRule

RULE = ArrayUTypecodeRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_array_u_basic():
    src = "import array\narray.array('u', 'hello')\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY083"


def test_array_u_no_initializer():
    src = "import array\narray.array('u')\n"
    assert len(_findings(src)) == 1


def test_module_alias():
    src = "import array as arr\narr.array('u', 'hello')\n"
    assert len(_findings(src)) == 1


def test_array_u_in_function():
    src = (
        "import array\n"
        "def make():\n"
        "    return array.array('u', 'hello')\n"
    )
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_array_b():
    src = "import array\narray.array('b', [1, 2])\n"
    assert _findings(src) == []


def test_array_i():
    src = "import array\narray.array('i', [1, 2, 3])\n"
    assert _findings(src) == []


def test_array_no_args():
    src = "import array\narray.array()\n"
    assert _findings(src) == []


def test_unrelated_array_call():
    src = "myarray('u')\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []