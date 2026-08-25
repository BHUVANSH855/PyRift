"""
PPY011 — array.array type code 'u' removed on PyPy / Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The 'u' type code (Unicode character) in array.array was deprecated
in Python 3.3 and removed in Python 3.13. PyPy follows the CPython
3.10 spec but behaviour around deprecated type codes differs.
Code using array.array('u', ...) silently fails on newer runtimes.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class ArrayTypeCodeRule(BaseRule):
    rule_id = "PPY011"
    title   = "array.array('u') type code removed in Python 3.13"
    runtime = "both"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            is_array = False
            if (isinstance(func, ast.Attribute) and
                    func.attr == "array" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "array") or isinstance(func, ast.Name) and func.id == "array":
                is_array = True

            if not is_array:
                continue

            # Check first argument is the 'u' type code
            if n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "u":
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "array.array('u') uses the Unicode type code which "
                            "was deprecated in Python 3.3 and removed in "
                            "Python 3.13. On PyPy, behaviour around this "
                            "deprecated type code may also differ from CPython."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.BOTH,
                        affected_from="3.13",
                        suggestion=(
                            "Replace array.array('u') with array.array('w') "
                            "for wide Unicode characters (Python 3.13+), "
                            "or use a list or str instead."
                        ),
                        docs_url=(
                            "https://docs.python.org/3/library/array.html"
                        ),
                    ))
        return findings