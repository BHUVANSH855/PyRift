"""Tests for PPY054 -- memoryview over bytearray/BytesIO resize behaviour on PyPy."""
from __future__ import annotations

import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy054_memoryview_buffer_error import MemoryviewBufferErrorRule

RULE = MemoryviewBufferErrorRule()
def parse(src): return ast.parse(textwrap.dedent(src))
def run(src): return RULE.check(parse(src), "<test>")

class TestPPY054:
    def test_memoryview_of_variable(self):
        f = run("buf = bytearray(b'hello')\nmv = memoryview(buf)\n")
        assert len(f) == 1 and f[0].rule_id == "PPY054"

    def test_severity_is_warning(self):
        assert run("buf = bytearray(b'x')\nmv = memoryview(buf)\n")[0].severity == Severity.WARNING

    def test_suggestion_mentions_release(self):
        assert "release" in run("buf = bytearray(b'x')\nmemoryview(buf)\n")[0].suggestion.lower()

    def test_runtime_is_pypy(self):
        from pyrift.finding import Runtime
        assert run("buf = bytearray(b'x')\nmemoryview(buf)\n")[0].runtime == Runtime.PYPY

    def test_rule_id(self):
        assert run("b = bytearray()\nmemoryview(b)\n")[0].rule_id == "PPY054"

    def test_memoryview_of_literal_not_flagged(self):
        assert run("mv = memoryview(b'hello')\n") == []

    def test_empty_file(self):
        assert run("") == []
