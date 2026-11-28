"""Tests for CPY085 -- codecs.open() deprecated 3.14."""
from __future__ import annotations

import ast
from urllib.parse import urlparse

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


# --- Metadata assertions ---

def test_affected_from_is_3_14():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert f[0].affected_from == "3.14"


def test_affected_until_is_empty():
    # No removal version scheduled — pending removal in future
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert not f[0].affected_until


def test_severity_is_warning():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    from pyrift.finding import Severity
    assert f[0].severity == Severity.WARNING


def test_description_names_deprecated_function():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert "codecs.open" in f[0].description


def test_description_mentions_replacement():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert "open()" in f[0].description


def test_suggestion_mentions_encoding_kwarg():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert "encoding" in f[0].suggestion


def test_docs_url_is_set():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert f[0].docs_url
    host = urlparse(f[0].docs_url).hostname
    assert host and (host == "python.org" or host.endswith(".python.org"))


def test_rule_id_is_cpy085():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert f[0].rule_id == "CPY085"


def test_description_mentions_deprecation_version():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert "3.14" in f[0].description, (
        "Description should mention the deprecation version 3.14"
    )


def test_affected_until_is_exactly_empty_string():
    # affected_until="" means no scheduled removal (not just falsy)
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert f[0].affected_until == "", (
        f"No removal date scheduled; expected '', got {f[0].affected_until!r}"
    )


def test_suggestion_mentions_open():
    src = "import codecs\ncodecs.open('f', 'r', 'utf-8')\n"
    f = _findings(src)
    assert "open" in f[0].suggestion


# --- Additional true positives ---

def test_codecs_open_in_function_body():
    src = (
        "import codecs\n"
        "def read_file(path):\n"
        "    return codecs.open(path, 'r', 'utf-8')\n"
    )
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY085"


def test_two_codecs_open_calls_two_findings():
    src = (
        "import codecs\n"
        "codecs.open('a.txt', 'r', 'utf-8')\n"
        "codecs.open('b.txt', 'w', 'utf-8')\n"
    )
    f = _findings(src)
    assert len(f) == 2


def test_codecs_open_no_args_still_flagged():
    # Even a bare codecs.open() call (syntactically valid) should be flagged
    src = "import codecs\ncodecs.open()\n"
    f = _findings(src)
    assert len(f) == 1


def test_codecs_open_keyword_only():
    src = "import codecs\ncodecs.open(file='f', mode='r', encoding='utf-8')\n"
    f = _findings(src)
    assert len(f) == 1


def test_codecs_open_as_assignment():
    src = (
        "import codecs\n"
        "fh = codecs.open('data.txt', encoding='latin-1')\n"
    )
    f = _findings(src)
    assert len(f) == 1


# --- Additional true negatives ---

def test_codecs_decode_not_flagged():
    src = "import codecs\ncodecs.decode(b'hello', 'utf-8')\n"
    assert _findings(src) == []


def test_codecs_lookup_not_flagged():
    src = "import codecs\ncodecs.lookup('utf-8')\n"
    assert _findings(src) == []


def test_unimported_codecs_attribute_access_not_flagged():
    # Without an import alias tracked, bare `open()` on unknown obj should not fire
    src = "x.open('file.txt', 'r', 'utf-8')\n"
    assert _findings(src) == []