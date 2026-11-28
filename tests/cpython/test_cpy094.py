"""Tests for CPY094 -- abc deprecated decorators raise DeprecationWarning in 3.14."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy094_abc_deprecated_decorators import (
    AbcDeprecatedDecoratorsRule,
)

RULE = AbcDeprecatedDecoratorsRule()
def _findings(src): return RULE.check(ast.parse(src), "test.py")

def test_abstractclassmethod_qualified():
    f = _findings("import abc\nclass Foo:\n    @abc.abstractclassmethod\n    def meth(cls): ...\n")
    assert len(f) == 1 and f[0].rule_id == "CPY094" and "abstractclassmethod" in f[0].description

def test_abstractstaticmethod_qualified():
    f = _findings("import abc\nclass Foo:\n    @abc.abstractstaticmethod\n    def meth(): ...\n")
    assert len(f) == 1

def test_abstractproperty_qualified():
    f = _findings("import abc\nclass Foo:\n    @abc.abstractproperty\n    def prop(self): ...\n")
    assert len(f) == 1

def test_abstractclassmethod_bare():
    f = _findings("from abc import abstractclassmethod\nclass Foo:\n    @abstractclassmethod\n    def meth(cls): ...\n")
    assert len(f) == 1

def test_all_three_in_one_class():
    src = "import abc\nclass Foo:\n    @abc.abstractclassmethod\n    def a(cls): ...\n    @abc.abstractstaticmethod\n    def b(): ...\n    @abc.abstractproperty\n    def c(self): ...\n"
    assert len(_findings(src)) == 3

def test_suggestion_contains_stacked_form():
    f = _findings("import abc\nclass Foo:\n    @abc.abstractclassmethod\n    def meth(cls): ...\n")
    assert "classmethod" in f[0].suggestion.lower()

def test_affected_from():
    f = _findings("import abc\nclass Foo:\n    @abc.abstractproperty\n    def p(self): ...\n")
    assert f[0].affected_from == "3.14"

def test_abstractmethod_not_flagged():
    assert _findings("import abc\nclass Foo:\n    @abc.abstractmethod\n    def meth(self): ...\n") == []

def test_property_not_flagged():
    assert _findings("class Foo:\n    @property\n    def p(self): ...\n") == []

def test_classmethod_not_flagged():
    assert _findings("class Foo:\n    @classmethod\n    def meth(cls): ...\n") == []

def test_empty_file():
    assert _findings("") == []
