"""Tests for CPY084 -- urllib.request.URLopener/FancyURLopener removed 3.14."""
from __future__ import annotations

import ast

from pyrift.finding import Severity
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


def test_other_module_urlopener_not_flagged():
    # Only urllib.request is the target module
    src = "from mylib.request import URLopener"
    assert _findings(src) == []


# --- Metadata: affected_from (removal rule — no affected_until) ---

def test_affected_from_is_3_14():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert f.affected_from == "3.14", (
        f"URLopener removed in 3.14; got {f.affected_from!r}"
    )


def test_affected_until_is_empty():
    # Removal rule — fires forever from 3.14, no upper bound
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert f.affected_until == "", (
        f"Removal rule; affected_until should be empty, got {f.affected_until!r}"
    )


# --- Severity: ERROR (removed, not just deprecated) ---

def test_severity_is_error():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert f.severity == Severity.ERROR, (
        f"URLopener is removed; severity should be ERROR, got {f.severity!r}"
    )


# --- Description content ---

def test_description_names_class_urlopener():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert "URLopener" in f.description


def test_description_names_class_fancyurlopener():
    src = "from urllib.request import FancyURLopener"
    f = _findings(src)[0]
    assert "FancyURLopener" in f.description


def test_description_mentions_removal_version():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert "3.14" in f.description


def test_description_mentions_original_deprecation():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert "3.3" in f.description


# --- Suggestion ---

def test_suggestion_mentions_urlopen():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert "urlopen" in f.suggestion


# --- docs_url ---

def test_docs_url_points_to_3_14_removed():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert "3.14" in f.docs_url or "removed" in f.docs_url


def test_docs_url_contains_urllib():
    # The docs URL should reference urllib or the whatsnew page, not an unrelated page
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert f.docs_url != "", "docs_url must not be empty for a removal rule"


# --- Rule ID ---

def test_rule_id_is_cpy084():
    src = "from urllib.request import URLopener"
    f = _findings(src)[0]
    assert f.rule_id == "CPY084"


# --- Additional true positives ---

def test_fancyurlopener_with_alias():
    src = "from urllib.request import FancyURLopener as FUO"
    f = _findings(src)
    assert len(f) == 1
    assert "FancyURLopener" in f[0].description


def test_import_star_not_flagged():
    # Star imports cannot be statically resolved to specific names
    src = "from urllib.request import *"
    assert _findings(src) == []


def test_urlopener_in_function_body():
    src = """
def setup():
    from urllib.request import URLopener
"""
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY084"


def test_both_findings_have_error_severity():
    # Both URLopener and FancyURLopener are removal-level findings
    src = "from urllib.request import URLopener, FancyURLopener"
    findings = _findings(src)
    assert len(findings) == 2
    assert all(fi.severity == Severity.ERROR for fi in findings), (
        "Both removed classes must produce ERROR severity"
    )


def test_suggestion_consistent_across_both_classes():
    # Both findings should reference urlopen as the replacement
    src = "from urllib.request import URLopener, FancyURLopener"
    findings = _findings(src)
    assert len(findings) == 2
    assert all("urlopen" in fi.suggestion for fi in findings), (
        "Suggestion for both classes should mention urlopen"
    )


def test_fancyurlopener_description_mentions_removal_version():
    src = "from urllib.request import FancyURLopener"
    f = _findings(src)[0]
    assert "3.14" in f.description, (
        "FancyURLopener finding should mention removal version 3.14"
    )


def test_fancyurlopener_affected_from_is_3_14():
    src = "from urllib.request import FancyURLopener"
    f = _findings(src)[0]
    assert f.affected_from == "3.14", (
        f"FancyURLopener removed in 3.14; got {f.affected_from!r}"
    )