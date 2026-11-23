"""Tests for CPY080 -- shutil.rmtree(onerror=) removed in 3.14."""
from __future__ import annotations

import ast

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