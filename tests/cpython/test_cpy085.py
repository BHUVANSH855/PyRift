"""Tests for CPY085 -- codecs.open() deprecated 3.14."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy085_codecs_open import CodecsOpenRule

RULE = CodecsOpenRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_codecs_open_basic():
    src = "import codecs\ncodecs.open('file.txt', 'r', 'utf-8')\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY085"


def test_codecs_open_as_expression():
    src = (
        "import codecs\n"
        "with codecs.open('file.txt', encoding='utf-8') as f:\n"
        "    pass\n"
    )
    assert len(_findings(src)) == 1


def test_module_alias():
    src = "import codecs as cd\ncd.open('file.txt', 'r', 'utf-8')\n"
    assert len(_findings(src)) == 1


def test_codecs_open_in_loop():
    src = (
        "import codecs\n"
        "for name in names:\n"
        "    codecs.open(name, 'r', 'utf-8')\n"
    )
    assert len(_findings(src)) == 1


# --- True negatives ---

def test_builtin_open():
    src = "open('file.txt', 'r')\n"
    assert _findings(src) == []


def test_io_open():
    src = "import io\nio.open('file.txt', 'r')\n"
    assert _findings(src) == []


def test_codecs_encode():
    src = "import codecs\ncodecs.encode('hello', 'utf-8')\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []