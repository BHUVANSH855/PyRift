"""
PPY058 -- type.__mro__ / type.mro() order can differ for C-extension types on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When a class inherits from C-extension types (int, float, list, dict, etc.),
the MRO computed by C3 linearisation can differ between CPython and PyPy
because PyPy implements those types in RPython rather than C.

Documentation:
  https://doc.pypy.org/en/latest/cpython_differences.html
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypeMroCExtRule(BaseRule):
    rule_id = "PPY058"
    title = "type.__mro__ / type.mro() order may differ for C-extension bases on PyPy"
    runtime = "pypy"
    severity = Severity.INFO

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if (
                isinstance(n, ast.Attribute)
                and n.attr == "__mro__"
                and isinstance(n.value, ast.Name)
            ):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "Direct inspection of __mro__ can produce "
                        "runtime-specific results when any base class is "
                        "implemented in C (CPython) or RPython (PyPy). "
                        "The C3 linearisation for mixed C/Python hierarchies "
                        "is not always identical across runtimes."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "If you need to find the next class in the MRO, use "
                        "super() instead of walking __mro__ manually. "
                        "If you need to check whether a class appears in the "
                        "MRO, use issubclass() rather than 'Cls in X.__mro__'."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "mro"
                and not n.args
                and not n.keywords
            ):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "Calling .mro() explicitly returns the C3 MRO list. "
                        "For classes that inherit from C-extension types "
                        "(int, list, dict, …), the returned order may differ "
                        "between CPython and PyPy."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use super() or issubclass() where possible. "
                        "If you must inspect .mro(), add a cross-runtime test "
                        "that asserts the expected order on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
