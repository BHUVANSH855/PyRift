"""Tests for CPY082 -- tarfile extraction without filter= (3.12–3.13)."""
from __future__ import annotations

import ast

from pyrift.finding import Severity
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


def test_multiple_extractions():
    src = (
        "import tarfile\n"
        "with tarfile.open('a.tar') as tf:\n"
        "    tf.extract('a.txt')\n"
        "    tf.extractall('/tmp')\n"
    )
    assert len(_findings(src)) == 2


def test_extractall_no_args():
    """extractall() with no arguments at all fires too."""
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractall()\n"
    )
    assert len(_findings(src)) == 1


def test_extractall_positional_path_no_filter():
    """Positional path arg but no filter= kwarg must still fire."""
    src = (
        "import tarfile\n"
        "tf.extractall('/dst')\n"
    )
    assert len(_findings(src)) == 1


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


def test_extractall_with_fully_trusted_filter():
    # filter= is explicit (intentional) — not flagged
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractall('/tmp', filter='fully_trusted')\n"
    )
    assert _findings(src) == []


def test_extractfile_not_flagged():
    # extractfile() has no filter= parameter — it returns a file-like object
    # and never writes to disk. Flagging it would be a false positive.
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractfile('file.txt')\n"
    )
    assert _findings(src) == [], (
        "extractfile() takes no filter= argument; it must not be flagged"
    )


def test_unrelated_method():
    src = "tf.getnames()\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []


def test_add_method_not_flagged():
    # tarfile.add() has a filter= param but it's a member-transform callback,
    # unrelated to extraction safety — must not be flagged
    src = (
        "import tarfile\n"
        "with tarfile.open('out.tar', 'w') as tf:\n"
        "    tf.add('/some/dir')\n"
    )
    assert _findings(src) == []


def test_extractall_with_members_no_filter():
    """members= kwarg present but filter= absent — still fires."""
    src = (
        "import tarfile\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractall('/tmp', members=tf.getmembers())\n"
    )
    assert len(_findings(src)) == 1


def test_extract_filter_variable():
    """filter= passed as a variable expression counts as explicit."""
    src = (
        "import tarfile\n"
        "flt = 'data'\n"
        "with tarfile.open('x.tar') as tf:\n"
        "    tf.extractall('/tmp', filter=flt)\n"
    )
    assert _findings(src) == []


# --- Metadata: affected_from / affected_until ---

def test_affected_from_is_3_12():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert f.affected_from == "3.12", (
        f"filter= deprecated in 3.12; got {f.affected_from!r}"
    )


def test_affected_until_is_3_13():
    # In Python 3.14 the default changed to 'data' and the warning was removed
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert f.affected_until == "3.13", (
        f"DeprecationWarning removed in 3.14; affected_until should be '3.13', got {f.affected_until!r}"
    )


# --- Severity ---

def test_severity_is_warning():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert f.severity == Severity.WARNING


# --- Description content ---

def test_description_names_method():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert "extractall" in f.description


def test_description_mentions_cve():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert "CVE-2007-4559" in f.description or "path traversal" in f.description.lower()


def test_description_mentions_3_14_default_change():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert "3.14" in f.description


# --- Suggestion content ---

def test_suggestion_mentions_data_filter():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert "data" in f.suggestion


# --- docs_url ---

def test_docs_url_points_to_extraction_filters():
    src = "import tarfile\ntf.extractall('/tmp')\n"
    f = _findings(src)[0]
    assert "tarfile" in f.docs_url
    assert "extraction-filter" in f.docs_url or "filter" in f.docs_url