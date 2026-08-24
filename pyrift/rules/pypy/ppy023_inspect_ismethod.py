"""
PPY023 — inspect.ismethod() returns different results on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, inspect.ismethod() returns False for built-in method
wrappers (like [].__add__). On PyPy, [].__add__ is a normal method
object, so inspect.ismethod([].__add__) returns True. Code using
inspect.ismethod() to distinguish built-in from Python methods
will behave differently on PyPy.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class InspectIsMethodRule(BaseRule):
    rule_id = "PPY023"
    title   = "inspect.ismethod() returns different results on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "ismethod" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "inspect"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "inspect.ismethod() behaves differently on PyPy. "
                        "On CPython, built-in method wrappers like "
                        "[].__add__ are not considered methods. On PyPy, "
                        "they are normal method objects and ismethod() "
                        "returns True. Code inspecting built-in types "
                        "may silently produce wrong results on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use callable() instead of inspect.ismethod() for "
                        "checking if something can be called. If you need "
                        "to distinguish built-in from Python methods, test "
                        "explicitly with inspect.isbuiltin()."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings