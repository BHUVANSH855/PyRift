"""Tests for CPY079 -- typing.ByteString / collections.abc.ByteString deprecated."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy079_bytestring_deprecated import ByteStringDeprecatedRule

RULE = ByteStringDeprecatedRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_typing_bytestring_import():
    src = "from typing import ByteString"
    assert len(_findings(src)) == 1
    assert _findings(src)[0].rule_id == "CPY079"


def test_collections_abc_bytestring_import():
    src = "from collections.abc import ByteString"
    assert len(_findings(src)) == 1


def test_typing_bytestring_with_alias():
    src = "from typing import ByteString as BS"
    assert len(_findings(src)) == 1


def test_collections_abc_bytestring_with_alias():
    src = "from collections.abc import ByteString as BS"
    assert len(_findings(src)) == 1


def test_multiple_imports_one_bytestring():
    src = "from typing import ByteString, Sequence, List"
    assert len(_findings(src)) == 1


def test_multiple_bytestring_imports():
    src = (
        "from typing import ByteString\n"
        "from collections.abc import ByteString\n"
    )
    assert len(_findings(src)) == 2


# --- True negatives ---

def test_no_bytestring():
    src = "from typing import Sequence"
    assert _findings(src) == []


def test_unrelated_import():
    src = "import os"
    assert _findings(src) == []


def test_bytearray_not_flagged():
    src = "from typing import ByteString\nx = bytearray(b'hello')"
    # Only the import line should be flagged, not bytearray usage
    assert len(_findings(src)) == 1


def test_empty_file():
    assert _findings("") == []