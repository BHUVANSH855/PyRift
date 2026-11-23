"""Tests for CPY088 -- sre_compile/sre_constants/sre_parse removed 3.15."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy088_sre_modules_removed import SreModulesRemovedRule

RULE = SreModulesRemovedRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_import_sre_compile():
    src = "import sre_compile"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY088"


def test_import_sre_constants():
    src = "import sre_constants"
    assert len(_findings(src)) == 1


def test_import_sre_parse():
    src = "import sre_parse"
    assert len(_findings(src)) == 1


def test_from_sre_compile():
    src = "from sre_compile import compile"
    assert len(_findings(src)) == 1


def test_from_sre_constants():
    src = "from sre_constants import MAXREPEAT"
    assert len(_findings(src)) == 1


def test_all_three():
    src = (
        "import sre_compile\n"
        "import sre_constants\n"
        "import sre_parse\n"
    )
    assert len(_findings(src)) == 3


# --- True negatives ---

def test_import_re():
    src = "import re"
    assert _findings(src) == []


def test_from_re():
    src = "from re import compile"
    assert _findings(src) == []


def test_unrelated_import():
    src = "import os"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []