"""
CPY055 — NotImplemented in boolean context raises TypeError in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since Python 3.9, using NotImplemented in a boolean context raised
DeprecationWarning. In Python 3.14, this became a hard TypeError.
Code using 'if NotImplemented:' or 'not NotImplemented' now crashes.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class NotImplementedBoolRule(BaseRule):
    rule_id = "CPY055"
    title   = "NotImplemented in boolean context raises TypeError in Python 3.14"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect: if NotImplemented: ...
            if isinstance(n, ast.If):
                test = n.test
                if (isinstance(test, ast.Name) and
                        test.id == "NotImplemented") or (isinstance(test, ast.UnaryOp) and
                        isinstance(test.op, ast.Not) and
                        isinstance(test.operand, ast.Name) and
                        test.operand.id == "NotImplemented"):
                    findings.append(self._make(filename, n))

            # Detect: bool(NotImplemented)
            if isinstance(n, ast.Call):
                func = n.func
                if (
                    isinstance(func, ast.Name)
                    and func.id == "bool"
                    and n.args
                    and isinstance(n.args[0], ast.Name)
                    and n.args[0].id == "NotImplemented"
                ):
                        findings.append(self._make(filename, n))

        return findings

    def _make(self, filename: str, n: ast.AST) -> Finding:
        return Finding(
            file=filename,
            line=n.lineno,  # type: ignore[attr-defined]
            col=n.col_offset,  # type: ignore[attr-defined]
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "NotImplemented is used in a boolean context. "
                "Since Python 3.9 this raised DeprecationWarning. "
                "In Python 3.14, using NotImplemented in a boolean "
                "context raises TypeError — this is now a hard error "
                "that crashes the program."
            ),
            severity=Severity.ERROR,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Do not use NotImplemented in boolean context. "
                "NotImplemented should only be returned from dunder "
                "methods (__add__, __eq__, etc.) to signal that the "
                "operation is not implemented for the given types. "
                "Use NotImplementedError for raising errors."
            ),
            docs_url=(
                "https://docs.python.org/3/whatsnew/3.14.html"
            ),
        )