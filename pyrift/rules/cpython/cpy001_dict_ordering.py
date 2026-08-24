"""
CPY001 — Dict ordering assumption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Code that compares dict.keys() / dict.values() / dict.items() with a
hard-coded LIST or TUPLE assumes insertion-order — only guaranteed
from CPython 3.7+. On CPython <3.7 and PyPy <7.3 this silently
produces wrong results.

NOTE: Comparing dict views with a set or frozenset is safe and
order-independent — pyrift does NOT flag those comparisons.

The real risk pattern is:
    list(d.keys()) == ['a', 'b']   # assumes order
    d.keys() == ['a', 'b']        # always False (type mismatch) but misleading intent
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DictOrderingRule(BaseRule):
    rule_id = "CPY001"
    title   = "Dict ordering assumption — comparing dict view to ordered sequence"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Compare):
                continue

            # Check left side is a dict view call
            if not self._is_dict_view_call(n.left):
                continue

            # Check right side — only flag if comparing to list or tuple
            # Comparing to set/frozenset is safe (order-independent)
            for comparator in n.comparators:
                if self._is_ordered_sequence(comparator):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "Comparing a dict view (keys/values/items) to a list "
                            "or tuple implies an assumption about insertion order. "
                            "Dict insertion order is only guaranteed on CPython 3.7+ "
                            "and PyPy 7.3+. On older runtimes the comparison may "
                            "silently return the wrong result. "
                            "Note: comparing to a set is safe and will not be flagged."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.BOTH,
                        affected_from="3.0",
                        affected_until="3.6",
                        suggestion=(
                            "Use set() for unordered comparison: "
                            "set(d.keys()) == {'a', 'b'}  "
                            "or sort both sides if order genuinely matters: "
                            "sorted(d.keys()) == sorted(expected)"
                        ),
                        docs_url=(
                            "https://docs.python.org/3/library/stdtypes.html#dict"
                        ),
                    ))

        return findings

    @staticmethod
    def _is_dict_view_call(node: ast.expr) -> bool:
        """Return True if node is d.keys(), d.values(), or d.items()."""
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                return func.attr in ("keys", "values", "items")
        return False

    @staticmethod
    def _is_ordered_sequence(node: ast.expr) -> bool:
        """
        Return True if node is a list or tuple literal.
        Return False for set/frozenset — those are order-independent and safe.
        """
        # Direct list or tuple literal: [1, 2] or (1, 2)
        if isinstance(node, (ast.List, ast.Tuple)):
            return True
        # set() call — safe, don't flag
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in ("set", "frozenset"):
                return False
        # Set literal: {'a', 'b'} — safe, don't flag
        if isinstance(node, ast.Set):
            return False
        return False