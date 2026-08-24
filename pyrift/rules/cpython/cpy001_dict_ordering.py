"""
CPY001 — Dict ordering assumption
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Code that compares dict.keys() / dict.values() / dict.items() with a
hard-coded list or tuple assumes insertion-order — only guaranteed
from CPython 3.7+. On CPython <3.7 and PyPy <7.3 this silently
produces wrong results.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class DictOrderingRule(BaseRule):
    rule_id = "CPY001"
    title   = "Dict ordering assumption"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Compare):
                continue
            if self._is_dict_view_call(n.left):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "Comparing dict view (keys/values/items) to an ordered "
                        "sequence assumes dict insertion order. Only guaranteed "
                        "on CPython 3.7+ and PyPy 7.3+. On older runtimes this "
                        "may silently return False even when contents are identical."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.BOTH,
                    affected_from="3.0",
                    affected_until="3.6",
                    suggestion=(
                        "Use set() for unordered comparison: "
                        "set(d.keys()) == {'a', 'b'}  "
                        "or sort both sides if order matters."
                    ),
                    docs_url="https://docs.python.org/3/library/stdtypes.html#dict",
                ))

        return findings

    @staticmethod
    def _is_dict_view_call(node: ast.expr) -> bool:
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                return func.attr in ("keys", "values", "items")
        return False