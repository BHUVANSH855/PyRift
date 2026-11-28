"""Tests for PPY058 -- type.__mro__ / type.mro() differences for C-ext bases on PyPy."""
from __future__ import annotations

import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy058_type_mro_c_ext import TypeMroCExtRule

RULE = TypeMroCExtRule()
def parse(src): return ast.parse(textwrap.dedent(src))
def run(src): return RULE.check(parse(src), "<test>")

class TestPPY058:
    def test_mro_attribute_access(self):
        f = run("mro = MyClass.__mro__\n")
        assert len(f) >= 1 and f[0].rule_id == "PPY058"

    def test_mro_method_call(self):
        f = run("order = MyClass.mro()\n")
        assert len(f) >= 1 and f[0].rule_id == "PPY058"

    def test_severity_is_info(self):
        assert run("mro = Cls.__mro__\n")[0].severity == Severity.INFO

    def test_suggestion_mentions_super(self):
        assert "super" in run("mro = Cls.__mro__\n")[0].suggestion.lower()

    def test_runtime_is_pypy(self):
        from pyrift.finding import Runtime
        assert run("mro = Cls.__mro__\n")[0].runtime == Runtime.PYPY

    def test_mro_in_loop(self):
        assert len(run("for cls in Base.__mro__:\n    pass\n")) >= 1

    def test_no_duplicate_on_same_line(self):
        f = run("x = A.__mro__\n")
        lines = [fi.line for fi in f]
        assert len(lines) == len(set(lines)) or len(lines) == 1

    def test_empty_file(self):
        assert run("") == []
