"""
PPY028 — readline.parse_and_bind() calls are ignored on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy's readline module was rewritten from scratch and is not GNU
readline. As a result, readline.parse_and_bind() calls are silently
ignored on PyPy. Code that configures readline keybindings will
appear to work but have no effect on PyPy.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class ReadlineParseBindRule(BaseRule):
    rule_id = "PPY028"
    title   = "readline.parse_and_bind() silently ignored on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "parse_and_bind" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "readline"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "readline.parse_and_bind() is called here. PyPy's "
                        "readline module is not GNU readline — it was "
                        "rewritten from scratch. parse_and_bind() calls "
                        "are silently ignored on PyPy. Keybinding "
                        "configuration will have no effect on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Guard with a runtime check: "
                        "if not hasattr(sys, '__pypy__'): "
                        "readline.parse_and_bind(...) "
                        "to avoid the silent no-op on PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings