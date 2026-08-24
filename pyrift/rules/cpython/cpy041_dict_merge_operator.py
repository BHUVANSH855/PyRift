"""
CPY041 — dict merge operator | requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The | operator for dict merging and |= for dict update were
added in Python 3.9 (PEP 584). Using them on 3.8 or below
raises TypeError at runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DictMergeOperatorRule(BaseRule):
    rule_id = "CPY041"
    title   = "dict | merge operator requires Python 3.9+"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect d1 | d2 where both sides look like dicts
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
                # Check if either operand is a dict literal or Name
                left_is_dict = isinstance(n.left, (ast.Dict, ast.Name))
                right_is_dict = isinstance(n.right, (ast.Dict, ast.Name))
                if left_is_dict and right_is_dict:
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "The | operator for dict merging was added in "
                            "Python 3.9 (PEP 584). Using it on Python 3.8 "
                            "or below raises TypeError at runtime."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.0",
                        affected_until="3.8",
                        suggestion=(
                            "For Python 3.8 compatibility use: "
                            "{**d1, **d2} for merging, or "
                            "d1.update(d2) for in-place update."
                        ),
                        docs_url="https://peps.python.org/pep-0584/",
                    ))
            # Detect d1 |= d2
            if isinstance(n, ast.AugAssign) and isinstance(n.op, ast.BitOr):
                if isinstance(n.target, ast.Name):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "The |= operator for dict update was added in "
                            "Python 3.9 (PEP 584). Using it on Python 3.8 "
                            "or below raises TypeError at runtime."
                        ),
                        severity=Severity.ERROR,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.0",
                        affected_until="3.8",
                        suggestion=(
                            "For Python 3.8 compatibility use: "
                            "d1.update(d2) instead of d1 |= d2."
                        ),
                        docs_url="https://peps.python.org/pep-0584/",
                    ))
        return findings