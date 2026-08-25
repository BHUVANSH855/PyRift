"""
PPY043 — __slots__ memory savings differ on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, __slots__ prevents __dict__ creation and saves memory
predictably. On PyPy, __slots__ still exists but the memory savings
are different because PyPy uses a different object layout (maps/hidden
classes). Code that relies on specific memory behaviour with __slots__
may behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class SlotsMemorypyRule(BaseRule):
    rule_id = "PPY043"
    title   = "__slots__ memory savings differ on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.ClassDef):
                continue
            for item in n.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if (isinstance(target, ast.Name) and
                                target.id == "__slots__"):
                            findings.append(Finding(
                                file=filename,
                                line=item.lineno,
                                col=item.col_offset,
                                rule_id=self.rule_id,
                                title=self.title,
                                description=(
                                    f"Class '{n.name}' defines __slots__. "
                                    "On PyPy, __slots__ works correctly for "
                                    "attribute access, but the memory savings "
                                    "differ from CPython because PyPy uses hidden "
                                    "classes (maps) for object layout. Measure "
                                    "memory independently on each runtime rather "
                                    "than assuming CPython's numbers apply to PyPy."
                                ),
                                severity=Severity.INFO,
                                runtime=Runtime.PYPY,
                                suggestion=(
                                    "__slots__ is still correct and beneficial "
                                    "on PyPy — just measure memory usage "
                                    "independently on each runtime rather than "
                                    "assuming CPython numbers apply."
                                ),
                                docs_url=(
                                    "https://doc.pypy.org/en/latest/"
                                    "cpython_differences.html"
                                ),
                            ))
        return findings