import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy054_int_trunc import IntTruncRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestCPY054:
    rule = IntTruncRule()

    def test_detects_trunc_method_without_int_or_index(self):
        src = """
class MyNumber:
    def __trunc__(self):
        return 0
"""
        findings = run(self.rule, src)

        assert len(findings) == 1
        assert findings[0].rule_id == "CPY054"
        assert findings[0].severity == Severity.ERROR

    def test_clean_int_method(self):
        src = """
class MyNumber:
    def __int__(self):
        return int(self._value)
"""
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_index_method(self):
        src = """
class MyNumber:
    def __index__(self):
        return self._value

    def __trunc__(self):
        return self._value
"""
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_when_class_defines_int_and_trunc(self):
        src = """
class MyNumber:
    def __int__(self):
        return int(self._value)

    def __trunc__(self):
        return int(self._value)
"""
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_clean_fraction_like_class(self):
        src = """
class FractionLike:
    def __int__(self):
        return self._numerator // self._denominator

    def __trunc__(self):
        return self._numerator // self._denominator
"""
        findings = run(self.rule, src)

        assert len(findings) == 0

    def test_suggestion_mentions_int(self):
        src = """
class X:
    def __trunc__(self):
        return 0
"""
        findings = run(self.rule, src)

        assert len(findings) == 1
        assert "__int__" in findings[0].suggestion

    def test_clean_abstract_trunc_method(self):
        src = """
from abc import abstractmethod

class RealLike:
    @abstractmethod
    def __trunc__(self):
        raise NotImplementedError
"""
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_clean_abstractmethod_attribute_trunc_method(self):
        src = """
import abc

class RealLike:
    @abc.abstractmethod
    def __trunc__(self):
        raise NotImplementedError
"""
        findings = run(self.rule, src)
        assert len(findings) == 0