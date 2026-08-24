"""
PPY024 — timeit reports average not minimum on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, the timeit module reports the minimum time across runs
(since minimum is considered most reliable). On PyPy, timeit reports
the average time and standard deviation instead, because PyPy's JIT
means the minimum is often misleading (JIT warmup skews results).
Code parsing timeit output may silently get different values on PyPy.
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class TimeitRule(BaseRule):
    rule_id = "PPY024"
    title   = "timeit reports average not minimum on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    if alias.name == "timeit":
                        findings.append(self._make(filename, n))
            elif isinstance(n, ast.ImportFrom):
                if n.module == "timeit":
                    findings.append(self._make(filename, n))
        return findings

    def _make(self, filename: str, n: ast.AST) -> Finding:
        return Finding(
            file=filename,
            line=n.lineno,
            col=n.col_offset,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "The timeit module is imported. On CPython, timeit reports "
                "the minimum time (least overhead). On PyPy, timeit reports "
                "the average and standard deviation because JIT warmup makes "
                "the minimum misleading. Code that parses or compares timeit "
                "output between runtimes will see different formats and values."
            ),
            severity=Severity.INFO,
            runtime=Runtime.PYPY,
            suggestion=(
                "When benchmarking across CPython and PyPy, account for "
                "PyPy's JIT warmup by running more iterations. Do not "
                "compare raw timeit output between runtimes directly."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/cpython_differences.html"
                "#miscellaneous"
            ),
        )