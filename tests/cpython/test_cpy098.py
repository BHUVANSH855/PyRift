"""Tests for CPY098 -- calendar.January / calendar.February deprecated in Python 3.13."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy098_calendar_deprecated_constants import (
    CalendarDeprecatedConstantsRule,
)

RULE = CalendarDeprecatedConstantsRule()
def _findings(src): return RULE.check(ast.parse(src), "test.py")

def test_calendar_january():
    f = _findings("import calendar\nx = calendar.January\n")
    assert len(f) == 1 and f[0].rule_id == "CPY098" and "JANUARY" in f[0].suggestion

def test_calendar_february():
    f = _findings("import calendar\nx = calendar.February\n")
    assert len(f) == 1 and "FEBRUARY" in f[0].suggestion

def test_both_constants():
    assert len(_findings("import calendar\nx = calendar.January\ny = calendar.February\n")) == 2

def test_in_expression():
    assert len(_findings("import calendar\nif m == calendar.January:\n    pass\n")) == 1

def test_severity_is_warning():
    from pyrift.finding import Severity
    f = _findings("import calendar\nx = calendar.January\n")
    assert f[0].severity == Severity.WARNING

def test_affected_from():
    f = _findings("import calendar\nx = calendar.January\n")
    assert f[0].affected_from == "3.13"

def test_calendar_monday():
    assert _findings("import calendar\nx = calendar.MONDAY\n") == []

def test_calendar_january_uppercase():
    assert _findings("import calendar\nx = calendar.JANUARY\n") == []

def test_calendar_february_uppercase():
    assert _findings("import calendar\nx = calendar.FEBRUARY\n") == []

def test_unrelated_january():
    assert _findings("myobj.January\n") == []

def test_empty_file():
    assert _findings("") == []
