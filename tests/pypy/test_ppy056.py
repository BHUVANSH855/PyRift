"""Tests for PPY056 -- __slots__ class missing __weakref__ slot failure timing on PyPy."""
from __future__ import annotations

import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy056_weakref_slotted import WeakrefSlottedRule

RULE = WeakrefSlottedRule()
def parse(src): return ast.parse(textwrap.dedent(src))
def run(src): return RULE.check(parse(src), "<test>")

class TestPPY056:
    def test_slots_without_weakref(self):
        f = run("class Foo:\n    __slots__ = ('x', 'y')\n")
        assert len(f) == 1 and f[0].rule_id == "PPY056" and "Foo" in f[0].description

    def test_severity_is_warning(self):
        assert run("class Foo:\n    __slots__ = ('x',)\n")[0].severity == Severity.WARNING

    def test_single_string_slot(self):
        assert len(run("class Foo:\n    __slots__ = 'x'\n")) == 1

    def test_list_slots(self):
        assert len(run("class Foo:\n    __slots__ = ['x', 'y']\n")) == 1

    def test_suggestion_mentions_weakref_slot(self):
        assert "__weakref__" in run("class Foo:\n    __slots__ = ('x',)\n")[0].suggestion

    def test_slots_with_weakref_slot(self):
        assert run("class Foo:\n    __slots__ = ('x', '__weakref__')\n") == []

    def test_no_slots(self):
        assert run("class Foo:\n    pass\n") == []

    def test_empty_slots(self):
        assert run("class Foo:\n    __slots__ = ()\n") == []

    def test_empty_file(self):
        assert run("") == []
