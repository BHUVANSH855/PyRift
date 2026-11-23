"""Tests for CPY090 -- profile module deprecated 3.15 (use cProfile)."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy090_profile_deprecated import ProfileDeprecatedRule

RULE = ProfileDeprecatedRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_import_profile():
    src = "import profile"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY090"


def test_from_profile_import():
    src = "from profile import Profile"
    assert len(_findings(src)) == 1


def test_from_profile_run():
    src = "from profile import run"
    assert len(_findings(src)) == 1


def test_profile_in_function():
    src = (
        "def analyze():\n"
        "    import profile\n"
        "    profile.run('main()')\n"
    )
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_import_cprofile():
    src = "import cProfile"
    assert _findings(src) == []


def test_from_cprofile():
    src = "from cProfile import Profile"
    assert _findings(src) == []


def test_unrelated_import():
    src = "import os"
    assert _findings(src) == []


def test_profile_string_not_import():
    src = 'profile = "something"\n'
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []