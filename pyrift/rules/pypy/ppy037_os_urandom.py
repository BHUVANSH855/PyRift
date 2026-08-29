"""
PPY037 — os.urandom() may block on PyPy on some platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, os.urandom() uses the best available source of
randomness (getrandom on Linux, /dev/urandom otherwise).
On some PyPy versions and platforms, os.urandom() may use
a different source or block unexpectedly at startup when
the entropy pool is not yet initialised.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class OsUrandomRule(BaseRule):
    rule_id = "PPY037"
    title   = "os.urandom() source may differ on PyPy"
    runtime = "pypy"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "urandom" and
                    isinstance(func.value, ast.Name) and
                    func.value.id == "os"):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "os.urandom() is called here. "
                        "For security-critical code, prefer the secrets "
                        "module which explicitly guarantees the best available "
                        "entropy source on all platforms including PyPy. "
                        "Note: this rule is based on observed PyPy behaviour "
                        "and is not formally documented in PyPy's differences page."
                    ),
                    severity=Severity.INFO,  # observed, not formally documented
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "For cryptographic purposes, use the secrets module "
                        "instead: secrets.token_bytes(n). "
                        "It uses the best available source on all platforms "
                        "and both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/secrets.html"
                    ),
                ))
        return findings