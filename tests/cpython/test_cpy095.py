"""Tests for CPY095 -- argparse.BooleanOptionalAction type/choices/metavar removed in 3.14."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy095_argparse_boolean_optional_removed import (
    ArgparseBooleanOptionalRemovedRule,
)

RULE = ArgparseBooleanOptionalRemovedRule()
def _findings(src): return RULE.check(ast.parse(src), "test.py")

def test_type_kwarg():
    f = _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction', type=int)\n")
    assert len(f) == 1 and f[0].rule_id == "CPY095" and "type" in f[0].description

def test_choices_kwarg():
    f = _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction', choices=[0,1])\n")
    assert len(f) == 1

def test_metavar_kwarg():
    f = _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction', metavar='BOOL')\n")
    assert len(f) == 1

def test_multiple_bad_kwargs():
    f = _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction', type=int, choices=[0,1], metavar='B')\n")
    assert len(f) == 1

def test_severity_is_error():
    from pyrift.finding import Severity
    f = _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction', type=str)\n")
    assert f[0].severity == Severity.ERROR

def test_affected_from():
    f = _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction', type=int)\n")
    assert f[0].affected_from == "3.14"

def test_no_bad_kwargs():
    assert _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--flag', action='BooleanOptionalAction')\n") == []

def test_other_action_with_type():
    assert _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--count', action='store', type=int)\n") == []

def test_no_action():
    assert _findings("import argparse\np = argparse.ArgumentParser()\np.add_argument('--count', type=int)\n") == []

def test_empty_file():
    assert _findings("") == []
