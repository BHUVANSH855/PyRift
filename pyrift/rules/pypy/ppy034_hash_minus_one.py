"""
PPY034 — hash() values may differ between CPython and PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, hash(-1) returns -2 because -1 is reserved as an
error indicator in CPython's C implementation. PyPy tries to
match this behaviour but there are edge cases where hash values
for certain objects differ between runtimes.

Only flag when the hash result is stored in a variable or used
in a comparison — those are the cases where a difference matters.
Using hash() purely as a dict key or set member is fine.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _is_hash_call(n: ast.AST) -> bool:
    return (
        isinstance(n, ast.Call) and
        isinstance(n.func, ast.Name) and
        n.func.id == "hash"
    )


class HashMinusOneRule(BaseRule):
    rule_id = "PPY034"
    title   = "hash() values may differ between CPython and PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Flag: h = hash(x) — storing hash result
            if isinstance(n, ast.Assign) and _is_hash_call(n.value):
                findings.append(self._make(filename, n.value))

            # Flag: if hash(x) == hash(y) — comparing hash values
            if isinstance(n, ast.Compare):
                if _is_hash_call(n.left):
                    findings.append(self._make(filename, n.left))
                for comp in n.comparators:
                    if _is_hash_call(comp):
                        findings.append(self._make(filename, comp))

            # Flag: x == hash(y) in augmented assign
            if isinstance(n, ast.AugAssign) and _is_hash_call(n.value):
                findings.append(self._make(filename, n.value))

        return findings

    def _make(self, filename: str, n: ast.AST) -> Finding:
        return Finding(
            file=filename,
            line=n.lineno,  # type: ignore[attr-defined]
            col=n.col_offset,  # type: ignore[attr-defined]
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "The result of hash() is stored or compared. On CPython, "
                "hash(-1) returns -2 because -1 is reserved in the C "
                "implementation. PyPy matches this for integers, but hash "
                "values for certain custom objects may differ between "
                "runtimes. Never persist hash values or compare them "
                "across different Python runtimes."
            ),
            severity=Severity.INFO,
            runtime=Runtime.PYPY,
            suggestion=(
                "Never store hash values persistently or compare them "
                "across different Python runtimes. Hash values are "
                "implementation-specific and not guaranteed to be "
                "consistent between CPython and PyPy."
            ),
            docs_url=(
                "https://doc.pypy.org/en/latest/cpython_differences.html"
                "#miscellaneous"
            ),
        )