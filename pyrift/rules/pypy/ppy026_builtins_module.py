"""
PPY026 — __builtins__ is always a module on PyPy, never a dict
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, __builtins__ is the __builtin__ module in the main
module but a dict in other modules. On PyPy, __builtins__ is
always the module, never a dict. Code that checks type(__builtins__)
or accesses __builtins__ as a dict will behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class BuiltinsModuleRule(BaseRule):
    rule_id = "PPY026"
    title   = "__builtins__ is always a module on PyPy, never a dict"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and n.id == "__builtins__":
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "__builtins__ is accessed here. On CPython, "
                        "__builtins__ is the __builtin__ module in __main__ "
                        "but a plain dict in other modules. On PyPy, "
                        "__builtins__ is always the module — never a dict. "
                        "Code checking isinstance(__builtins__, dict) or "
                        "accessing __builtins__['name'] will silently fail on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use the builtins module directly instead: "
                        "import builtins; builtins.print — this works "
                        "consistently on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings