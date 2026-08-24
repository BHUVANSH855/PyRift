"""
PPY012 — Subclassing C-implemented builtins behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, subclassing C-implemented types (like dict, list) and
overriding methods sometimes has subtle differences from PyPy.
Specifically, internal C-level calls may bypass overridden Python
methods on CPython but not on PyPy, or vice versa — leading to
silent behaviour differences.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

# Built-in types where internal method dispatch differs
DANGEROUS_BASES = {
    "dict", "list", "str", "int", "float",
    "tuple", "set", "frozenset", "bytes",
}

DANGEROUS_OVERRIDES = {
    "__getitem__", "__setitem__", "__delitem__",
    "__contains__", "__len__", "__iter__",
    "__missing__", "update", "append", "extend",
}


class SubclassingBuiltinsRule(BaseRule):
    rule_id = "PPY012"
    title   = "Overriding built-in methods may behave differently on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.ClassDef):
                continue

            # Check if class inherits from a dangerous built-in
            dangerous_base = None
            for base in n.bases:
                if isinstance(base, ast.Name) and base.id in DANGEROUS_BASES:
                    dangerous_base = base.id
                    break

            if not dangerous_base:
                continue

            # Check if any dangerous method is overridden
            for item in n.body:
                if (isinstance(item, ast.FunctionDef) and
                        item.name in DANGEROUS_OVERRIDES):
                    findings.append(Finding(
                        file=filename,
                        line=item.lineno,
                        col=item.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"Class '{n.name}' subclasses '{dangerous_base}' "
                            f"and overrides '{item.name}'. On CPython, internal "
                            "C-level calls to built-in methods may bypass Python "
                            "overrides. On PyPy, the same calls may go through "
                            "the Python override. This can cause silent behaviour "
                            "differences between runtimes."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Test the overridden method explicitly on both "
                            "CPython and PyPy. Consider using composition "
                            "instead of inheritance from built-in types."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                        ),
                    ))

        return findings