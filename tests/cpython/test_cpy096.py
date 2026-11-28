"""Tests for CPY096 -- threading.RLock() with arguments removed in 3.15."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy096_threading_rlock_args_removed import (
    ThreadingRLockArgsRemovedRule,
)

RULE = ThreadingRLockArgsRemovedRule()
def _findings(src): return RULE.check(ast.parse(src), "test.py")

def test_positional_arg():
    f = _findings("import threading\nthreading.RLock(1)\n")
    assert len(f) == 1 and f[0].rule_id == "CPY096"

def test_keyword_arg():
    assert len(_findings("import threading\nthreading.RLock(verbose=0)\n")) == 1

def test_multiple_args():
    assert len(_findings("import threading\nthreading.RLock(1, 2, x=3)\n")) == 1

def test_severity_is_error():
    from pyrift.finding import Severity
    f = _findings("import threading\nthreading.RLock(verbose=0)\n")
    assert f[0].severity == Severity.ERROR

def test_affected_from():
    f = _findings("import threading\nthreading.RLock(1)\n")
    assert f[0].affected_from == "3.15"

def test_aliased_import():
    assert len(_findings("import threading as t\nt.RLock(verbose=0)\n")) == 1

def test_no_args():
    assert _findings("import threading\nthreading.RLock()\n") == []

def test_other_lock():
    assert _findings("import threading\nthreading.Lock(1)\n") == []

def test_empty_file():
    assert _findings("") == []
