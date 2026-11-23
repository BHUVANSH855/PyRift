"""Tests for CPY082 -- tarfile extraction without filter= (3.12)."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy082_tarfile_extraction_filter import (
    TarfileExtractionFilterRule,
)

RULE = TarfileExtractionFilterRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_extractall_no_filter():
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractall('/tmp')\n"
    )
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY082"


def test_extract_no_filter():
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extract('file.txt', '/tmp')\n"
    )
    assert len(_findings(src)) == 1


def test_extractfile_no_filter():
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractfile('file.txt')\n"
    )
    assert len(_findings(src)) == 1


def test_multiple_extractions():
    src = (
        "import tarfile\n"
        "with tarfile.open('a.tar') as tf:\n"
        "    tf.extract('a.txt')\n"
        "    tf.extractall('/tmp')\n"
    )
    assert len(_findings(src)) == 2


# --- True negatives ---

def test_extractall_with_filter():
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractall('/tmp', filter='data')\n"
    )
    assert _findings(src) == []


def test_extract_with_filter():
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extract('file.txt', '/tmp', filter='tar')\n"
    )
    assert _findings(src) == []


def test_unrelated_method():
    src = "tf.getnames()\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []