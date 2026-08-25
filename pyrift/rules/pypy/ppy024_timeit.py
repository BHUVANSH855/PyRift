"""
PPY024 — timeit reports average not minimum on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, the timeit module reports the minimum time across runs.
On PyPy, timeit reports the average and standard deviation because
JIT warmup makes the minimum misleading.

Only flag when timeit output is parsed programmatically (stored in
a variable from Timer.timeit() or repeat()), not every import.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TimeitRule(BaseRule):
    rule_id = "PPY024"
    title   = "timeit reports average not minimum on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Flag when timeit()/repeat() result is stored — implies parsing output
            if not isinstance(n, ast.Assign):
                continue
            if not isinstance(n.value, ast.Call):
                continue
            func = n.value.func
            if isinstance(func, ast.Attribute) and func.attr in (
                "timeit", "repeat", "autorange"
            ):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The result of timeit/repeat is stored. On CPython, "
                        "timeit reports minimum time (least overhead). On PyPy, "
                        "timeit reports average and standard deviation because "
                        "JIT warmup makes the minimum misleading. Code that "
                        "parses or compares timeit results between runtimes "
                        "will see different formats and values."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "When benchmarking across CPython and PyPy, account "
                        "for PyPy's JIT warmup by running more iterations. "
                        "Do not compare raw timeit output between runtimes."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html#miscellaneous"
                    ),
                ))

        return findings