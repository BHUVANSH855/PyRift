"""Tests for CPY093 -- glob.glob0() / glob.glob1() removed 3.15."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy093_glob_removed import GlobRemovedRule

RULE = GlobRemovedRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_glob_glob0():
    src = "import glob\nglob.glob0('/tmp', '*.py')\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY093"


def test_glob_glob1():
    src = "import glob\nglob.glob1('/tmp', '*.py')\n"
    assert len(_findings(src)) == 1


def test_both_removed():
    src = (
        "import glob\n"
        "glob.glob0('/a', '*.py')\n"
        "glob.glob1('/b', '*.txt')\n"
    )
    assert len(_findings(src)) == 2


def test_module_alias_glob0():
    src = "import glob as g\ng.glob0('/tmp', '*.py')\n"
    assert len(_findings(src)) == 1


def test_module_alias_glob1():
    src = "import glob as g\ng.glob1('/tmp', '*.py')\n"
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_glob_glob():
    src = "import glob\nglob.glob('/tmp/*.py')\n"
    assert _findings(src) == []


def test_glob_iglob():
    src = "import glob\nglob.iglob('/tmp/*.py')\n"
    assert _findings(src) == []


def test_unrelated_glob():
    src = "myglob.glob0('/tmp', '*.py')\n"
    # Not using glob module
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []