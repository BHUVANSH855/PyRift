"""
PPY025 — Sets are ordered on PyPy, unordered on CPython < 3.7
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, sets have never been ordered. On PyPy, dictionaries
and sets are ordered. Code relying on set iteration order being
random/unspecified may produce different results across runtimes.
Also noted: on CPython 3.7+ dicts are ordered but sets still are not.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class SetOrderingRule(BaseRule):
    rule_id = "PPY025"
    title   = "Set iteration order differs between CPython and PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect: list(some_set) or sorted used on set
            # or for x in set_var pattern where set is a literal
            if isinstance(n, ast.Call):
                func = n.func
                if (isinstance(func, ast.Name) and
                        func.id == "list" and
                        n.args):
                    arg = n.args[0]
                    # list({...}) — converting set literal to list
                    if isinstance(arg, ast.Set):
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                "Converting a set to a list with list({...}). "
                                "On CPython, sets are unordered — iteration "
                                "order is not guaranteed. On PyPy, sets are "
                                "ordered by insertion. Code relying on set "
                                "iteration order will silently produce "
                                "different results across runtimes."
                            ),
                            severity=Severity.WARNING,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "Use sorted(your_set) if you need a "
                                "deterministic order — this works correctly "
                                "on both CPython and PyPy."
                            ),
                            docs_url=(
                                "https://doc.pypy.org/en/latest/"
                                "cpython_differences.html#miscellaneous"
                            ),
                        ))
        return findings