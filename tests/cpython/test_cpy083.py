"""Tests for CPY083 -- array.array('u', ...) deprecated 3.13, removed 3.16."""
from __future__ import annotations

import ast

from pyrift.finding import Severity
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


def test_array_u_assigned():
    src = "import array\nbuf = array.array('u')\n"
    assert len(_findings(src)) == 1


def test_two_array_u_calls_two_findings():
    src = (
        "import array\n"
        "a = array.array('u', 'hello')\n"
        "b = array.array('u', 'world')\n"
    )
    assert len(_findings(src)) == 2


# --- True negatives ---

def test_array_b():
    src = "import array\narray.array('b', [1, 2])\n"
    assert _findings(src) == []


def test_array_i():
    src = "import array\narray.array('i', [1, 2, 3])\n"
    assert _findings(src) == []


def test_array_w_ok():
    # 'w' is the correct replacement for 'u'
    src = "import array\narray.array('w', 'hello')\n"
    assert _findings(src) == []


def test_array_no_args():
    src = "import array\narray.array()\n"
    assert _findings(src) == []


def test_unrelated_array_call():
    src = "myarray('u')\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []


def test_array_d_not_flagged():
    src = "import array\narray.array('d', [1.0, 2.0])\n"
    assert _findings(src) == []


def test_array_u_as_variable_not_detected():
    """Typecode passed as a variable can't be statically detected — no finding."""
    src = (
        "import array\n"
        "tc = 'u'\n"
        "array.array(tc, 'hello')\n"
    )
    assert _findings(src) == []


# --- Metadata: affected_from / affected_until ---

def test_affected_from_is_3_13():
    # Runtime DeprecationWarning starts in 3.13 (doc-only since 3.3)
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert f.affected_from == "3.13", (
        f"'u' type code emits DeprecationWarning from 3.13; got {f.affected_from!r}"
    )


def test_affected_until_is_3_16():
    # affected_until is the removal version (inclusive convention in this project)
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert f.affected_until == "3.16", (
        f"'u' type code removed in 3.16; affected_until should be '3.16', got {f.affected_until!r}"
    )


# --- Severity ---

def test_severity_is_warning():
    """Still pending removal in 3.16 — severity must be WARNING."""
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert f.severity == Severity.WARNING


# --- Description content ---

def test_description_mentions_deprecation_version():
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert "3.13" in f.description


def test_description_mentions_removal_version():
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert "3.16" in f.description


# --- Suggestion content ---

def test_suggestion_mentions_w_typecode():
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert "'w'" in f.suggestion or '"w"' in f.suggestion or " w " in f.suggestion or f.suggestion.endswith("'w'")


# --- docs_url ---

def test_docs_url_points_to_array():
    src = "import array\narray.array('u')\n"
    f = _findings(src)[0]
    assert "array" in f.docs_url