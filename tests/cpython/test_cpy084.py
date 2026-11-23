"""Tests for CPY084 -- urllib.request.URLopener/FancyURLopener removed 3.14."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy084_urllib_urlopen_deprecated import (
    UrllibUrlopenDeprecatedRule,
)

RULE = UrllibUrlopenDeprecatedRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_urlopener_import():
    src = "from urllib.request import URLopener"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY084"


def test_fancyurlopener_import():
    src = "from urllib.request import FancyURLopener"
    assert len(_findings(src)) == 1


def test_both_removed():
    src = "from urllib.request import URLopener, FancyURLopener"
    assert len(_findings(src)) == 2


def test_urlopener_with_alias():
    src = "from urllib.request import URLopener as UO"
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_urllib_request_ok():
    src = "from urllib.request import urlopen"
    assert _findings(src) == []


def test_urllib_request_request():
    src = "from urllib.request import Request"
    assert _findings(src) == []


def test_unrelated_urllib():
    src = "import urllib.parse"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []