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


def test_clean_memoryview_not_flagged():
    src = "from typing import Sequence\nx: memoryview"
    assert _findings(src) == []


def test_clean_buffer_not_flagged():
    src = "from collections.abc import Buffer"
    assert _findings(src) == []


def test_clean_bytearray_import_not_flagged():
    src = "import bytearray"
    assert _findings(src) == []


def test_clean_other_collections_abc_import():
    """Other names from collections.abc must not fire."""
    src = "from collections.abc import Sequence, MutableMapping, Iterator"
    assert _findings(src) == []


def test_clean_typing_other_names():
    src = "from typing import List, Dict, Optional, Union"
    assert _findings(src) == []


# --- Metadata: affected_from ---

def test_typing_affected_from_is_3_9():
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert f.affected_from == "3.9", (
        f"typing.ByteString was deprecated in 3.9; got {f.affected_from!r}"
    )


def test_collections_abc_affected_from_is_3_12():
    src = "from collections.abc import ByteString"
    f = _findings(src)[0]
    assert f.affected_from == "3.12", (
        f"collections.abc.ByteString was deprecated in 3.12; got {f.affected_from!r}"
    )


# --- Metadata: affected_until ---

def test_typing_affected_until_is_3_17():
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert f.affected_until == "3.17", (
        f"ByteString removal is in 3.17; got {f.affected_until!r}"
    )


def test_collections_abc_affected_until_is_3_17():
    src = "from collections.abc import ByteString"
    f = _findings(src)[0]
    assert f.affected_until == "3.17", (
        f"ByteString removal is in 3.17; got {f.affected_until!r}"
    )


# --- Metadata: severity ---

def test_severity_is_warning():
    """Still pending removal in 3.17 — severity must be WARNING."""
    src = "from typing import ByteString"
    assert _findings(src)[0].severity.name == "WARNING"


# --- Metadata: docs_url ---

def test_docs_url_points_to_pending_removal_3_17():
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert "pending-removal-in-3.17" in f.docs_url, (
        f"docs_url should reference pending-removal-in-3.17; got {f.docs_url!r}"
    )


# --- Description content ---

def test_description_names_module_and_deprecation_version_typing():
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert "typing.ByteString" in f.description
    assert "3.9" in f.description


def test_description_names_module_and_deprecation_version_collections():
    src = "from collections.abc import ByteString"
    f = _findings(src)[0]
    assert "collections.abc.ByteString" in f.description
    assert "3.12" in f.description


def test_description_mentions_removal_version():
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert "3.17" in f.description


def test_description_mentions_3_15_dunder_all_change():
    """3.15 removed ByteString from __all__ — description should note this."""
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert "3.15" in f.description or "__all__" in f.description


def test_suggestion_mentions_replacement():
    src = "from typing import ByteString"
    f = _findings(src)[0]
    assert "bytearray" in f.suggestion or "Buffer" in f.suggestion or "bytes" in f.suggestion