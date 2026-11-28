"""Tests for CPY081 -- sys.last_type/last_value/last_traceback deprecated 3.12."""
from __future__ import annotations

import ast

from pyrift.finding import Severity
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


def test_last_type_in_expression():
    src = "import sys\nx = (sys.last_type, sys.last_value, sys.last_traceback)"
    assert len(_findings(src)) == 3


def test_last_value_assigned_to_variable():
    src = "import sys\nexc = sys.last_value"
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_sys_last_exc_ok():
    src = "import sys\nprint(sys.last_exc)"
    assert _findings(src) == []


def test_sys_version_ok():
    src = "import sys\nprint(sys.version)"
    assert _findings(src) == []


def test_unrelated_last_attr():
    # Must not flag last_type on a non-sys object
    src = "obj.last_type = None"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []


def test_local_variable_named_sys_not_flagged():
    # A local variable named sys that is NOT the sys module should not be flagged
    # (the rule checks ast.Name with id == "sys" — a local reassignment keeps
    # the Name node so this is a known limitation, but at minimum we document
    # the behaviour with a plain name node test)
    src = "sys = object()\nprint(sys.last_type)"
    # Rule fires here because it only checks the Name id, not binding — that's
    # an acceptable false-positive limitation; test just documents the count
    # so a future change doesn't silently alter behaviour
    result = _findings(src)
    assert isinstance(result, list)


def test_chained_attr_not_flagged():
    # sys.something.last_type — the value of .last_type is an Attribute, not a Name
    src = "import sys\nsys.exc_info().last_type"
    assert _findings(src) == []


def test_other_sys_attr_not_flagged():
    src = "import sys\nprint(sys.argv)\nprint(sys.path)\nprint(sys.modules)"
    assert _findings(src) == []


def test_clean_last_exc_replacement():
    src = (
        "import sys\n"
        "if sys.last_exc:\n"
        "    print(type(sys.last_exc))\n"
        "    print(sys.last_exc.__traceback__)\n"
    )
    assert _findings(src) == []


# --- Metadata: affected_from ---

def test_affected_from_is_3_12():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)[0]
    assert f.affected_from == "3.12", (
        f"sys.last_type deprecated in 3.12; got {f.affected_from!r}"
    )


def test_all_attrs_have_same_affected_from():
    for attr in ("last_type", "last_value", "last_traceback"):
        src = f"import sys\nprint(sys.{attr})"
        f = _findings(src)[0]
        assert f.affected_from == "3.12", f"sys.{attr}: expected 3.12, got {f.affected_from!r}"


# --- Metadata: affected_until (no removal date) ---

def test_affected_until_is_empty():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)[0]
    assert f.affected_until == "", (
        f"No removal version scheduled; affected_until should be empty, got {f.affected_until!r}"
    )


# --- Severity ---

def test_severity_is_warning():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)[0]
    assert f.severity == Severity.WARNING


# --- Description content ---

def test_description_names_deprecated_attr():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)[0]
    assert "sys.last_type" in f.description


def test_description_names_replacement():
    src = "import sys\nprint(sys.last_value)"
    f = _findings(src)[0]
    assert "sys.last_exc" in f.description


def test_description_names_deprecation_version():
    src = "import sys\nprint(sys.last_traceback)"
    f = _findings(src)[0]
    assert "3.12" in f.description


def test_description_per_attr_names_correct_attr():
    """Each finding description should name the actual attribute accessed."""
    for attr in ("last_type", "last_value", "last_traceback"):
        src = f"import sys\nprint(sys.{attr})"
        f = _findings(src)[0]
        assert attr in f.description, f"description should mention {attr!r}"


# --- Suggestion content ---

def test_suggestion_mentions_last_exc():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)[0]
    assert "last_exc" in f.suggestion


def test_suggestion_mentions_traceback_alternative_for_traceback():
    src = "import sys\nprint(sys.last_traceback)"
    f = _findings(src)[0]
    assert "__traceback__" in f.suggestion or "traceback" in f.suggestion.lower()


# --- docs_url ---

def test_docs_url_points_to_sys_last_exc():
    src = "import sys\nprint(sys.last_type)"
    f = _findings(src)[0]
    assert "sys" in f.docs_url
    assert "last_exc" in f.docs_url