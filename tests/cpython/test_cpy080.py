"""Tests for CPY080 -- shutil.rmtree(onerror=) deprecated in 3.12."""
from __future__ import annotations

import ast

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy080_shutil_rmtree_onerror import ShutilRmtreeOnErrorRule

RULE = ShutilRmtreeOnErrorRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_onerror_kwarg_flagged():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x', onerror=print)\n"
    )
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY080"


def test_onerror_with_other_kwargs():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x', ignore_errors=True, onerror=print)\n"
    )
    assert len(_findings(src)) == 1


def test_onerror_in_function_body():
    src = (
        "import shutil\n"
        "def cleanup():\n"
        "    shutil.rmtree('/tmp/x', onerror=print)\n"
    )
    assert len(_findings(src)) == 1


def test_module_alias():
    src = (
        "import shutil as sh\n"
        "sh.rmtree('/tmp/x', onerror=print)\n"
    )
    assert len(_findings(src)) == 1


def test_onerror_with_lambda():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x', onerror=lambda f, p, e: None)\n"
    )
    assert len(_findings(src)) == 1


def test_two_calls_two_findings():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/a', onerror=print)\n"
        "shutil.rmtree('/tmp/b', onerror=print)\n"
    )
    assert len(_findings(src)) == 2


# --- True negatives ---

def test_rmtree_no_onerror():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x')\n"
    )
    assert _findings(src) == []


def test_rmtree_ignore_errors_only():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x', ignore_errors=True)\n"
    )
    assert _findings(src) == []


def test_rmtree_onexc_ok():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x', onexc=print)\n"
    )
    assert _findings(src) == []


def test_unrelated_function():
    src = "shutil.copy('/a', '/b')\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []


def test_unrelated_module_rmtree_not_flagged():
    # A local function called rmtree with onerror should not be flagged
    src = (
        "def rmtree(path, onerror=None):\n"
        "    pass\n"
        "rmtree('/tmp/x', onerror=print)\n"
    )
    assert _findings(src) == []


def test_other_shutil_function_not_flagged():
    src = (
        "import shutil\n"
        "shutil.copytree('/a', '/b', onerror=print)\n"
    )
    assert _findings(src) == []


def test_rmtree_positional_args_no_onerror():
    src = (
        "import shutil\n"
        "shutil.rmtree('/tmp/x', False)\n"
    )
    assert _findings(src) == []


# --- Metadata: affected_from ---

def test_affected_from_is_3_12():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert f.affected_from == "3.12", (
        f"onerror deprecated in 3.12; got {f.affected_from!r}"
    )


# --- Metadata: affected_until (no removal date scheduled) ---

def test_affected_until_is_empty():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert f.affected_until == "", (
        f"onerror has no scheduled removal; affected_until should be empty, got {f.affected_until!r}"
    )


# --- Severity: deprecation warning only, not an error ---

def test_severity_is_warning():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert f.severity == Severity.WARNING, (
        f"onerror is not removed (only deprecated); severity should be WARNING, got {f.severity!r}"
    )


# --- Description content ---

def test_description_mentions_deprecated_version():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert "3.12" in f.description


def test_description_no_false_removal_claim():
    # Must NOT claim onerror was removed in 3.14 (it wasn't)
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert "removed in Python 3.14" not in f.description
    assert "removed in 3.14" not in f.description


def test_description_mentions_onerror():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert "onerror" in f.description


def test_suggestion_mentions_onexc():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert "onexc" in f.suggestion


def test_suggestion_mentions_signature_change():
    """The callback signature changed — suggestion should warn about this."""
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    # suggestion should mention the difference between onerror and onexc callbacks
    assert "exception" in f.suggestion.lower() or "exc_info" in f.suggestion or "third" in f.suggestion.lower()


def test_docs_url_points_to_shutil_rmtree():
    src = "import shutil\nshutil.rmtree('/tmp/x', onerror=print)\n"
    f = _findings(src)[0]
    assert "shutil" in f.docs_url
    assert "rmtree" in f.docs_url