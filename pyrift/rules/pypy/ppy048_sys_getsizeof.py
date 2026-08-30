"""
PPY048 — sys.getsizeof() reports different sizes on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy's object model uses different memory layouts than CPython.
sys.getsizeof() returns different values for the same objects because:
  - PyPy objects have larger base overhead (dict, GC headers)
  - Small integers are pre-allocated differently
  - String interning affects size calculations
  - List/dict internal structures differ

Code that uses sys.getsizeof() for memory budgets, caching decisions,
or adaptive algorithms will behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SysGetsizeofRule(BaseRule):
    rule_id = "PPY048"
    title   = "sys.getsizeof() returns different values on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            # sys.getsizeof(x)
            if (isinstance(func, ast.Attribute)
                    and func.attr == "getsizeof"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "sys"):
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "sys.getsizeof() returns different values on PyPy "
                        "due to different object memory layouts. PyPy has "
                        "larger base overhead for dicts and GC headers, "
                        "and different internal structures for lists, dicts, "
                        "and strings."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Do not rely on exact sys.getsizeof() values for "
                        "memory budgets or caching decisions. Use relative "
                        "comparisons or memory profiling tools instead."
                    ),
                    docs_url="https://doc.pypy.org/en/latest/cpython_differences.html",
                ))
        return findings
