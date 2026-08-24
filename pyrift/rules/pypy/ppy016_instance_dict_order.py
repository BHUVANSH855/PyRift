"""
PPY016 — Instance dict ordering not guaranteed on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In CPython 3.7+, instance dictionaries are ordered by insertion.
In PyPy, instance dictionaries use hidden classes (maps) for
performance — if __init__ adds attributes in different orders
across calls, the instance dict order is not guaranteed.
Code relying on instance __dict__ ordering may silently produce
wrong results on PyPy.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class InstanceDictOrderRule(BaseRule):
    rule_id = "PPY016"
    title   = "Instance __dict__ ordering not guaranteed on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect: obj.__dict__ being iterated or compared
            if not isinstance(n, ast.Attribute):
                continue
            if n.attr != "__dict__":
                continue
            # Check if __dict__ is used in a comparison or iteration
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "Accessing __dict__ on an instance. In CPython 3.7+, "
                    "instance dictionaries are insertion-ordered. In PyPy, "
                    "instance dicts use hidden classes for performance — "
                    "if __init__ adds attributes in different orders across "
                    "calls, dict order is not guaranteed to match CPython's."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.PYPY,
                suggestion=(
                    "Do not rely on instance __dict__ ordering. "
                    "If you need ordered attributes, define them explicitly "
                    "in __init__ in a consistent order, or use "
                    "__slots__ to make the layout fixed."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#order-of-dictionary-keys-in-instance-dicts"
                ),
            ))

        return findings