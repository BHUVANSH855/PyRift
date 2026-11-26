"""Tests for CPY097 -- wave mark methods removed in Python 3.15."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy097_wave_mark_methods_removed import (
    WaveMarkMethodsRemovedRule,
)

RULE = WaveMarkMethodsRemovedRule()
def _findings(src): return RULE.check(ast.parse(src), "test.py")

def test_getmark():
    f = _findings("import wave\nwr = wave.open('a.wav')\nwr.getmark(1)\n")
    assert len(f) == 1 and f[0].rule_id == "CPY097"

def test_setmark():
    assert len(_findings("import wave\nww = wave.open('a.wav','w')\nww.setmark(1,0,'start')\n")) == 1

def test_getmarkers():
    assert len(_findings("import wave\nwr = wave.open('a.wav')\nwr.getmarkers()\n")) == 1

def test_all_three_methods():
    src = "import wave\nwr = wave.open('a.wav')\nwr.getmark(1)\nwr.setmark(1,0,'x')\nwr.getmarkers()\n"
    assert len(_findings(src)) == 3

def test_severity_is_error():
    from pyrift.finding import Severity
    f = _findings("import wave\nwr = wave.open('a.wav')\nwr.getmarkers()\n")
    assert f[0].severity == Severity.ERROR

def test_affected_from():
    f = _findings("import wave\nwr = wave.open('a.wav')\nwr.getmarkers()\n")
    assert f[0].affected_from == "3.15"

def test_getmark_without_wave_import():
    assert _findings("other_obj.getmark(1)\n") == []

def test_wave_read_write():
    assert _findings("import wave\nwith wave.open('a.wav','r') as wr:\n    frames = wr.readframes(1024)\n") == []

def test_empty_file():
    assert _findings("") == []
