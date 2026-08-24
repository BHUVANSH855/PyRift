"""
PPY041 — dict | operator available on PyPy 7.3.7+ only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The dict | merge operator (PEP 584) requires PyPy 7.3.7+
(which corresponds to CPython 3.9 compatibility). On older
PyPy versions, using | on dicts raises TypeError silently.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class DictMergePypyRule(BaseRule):
    rule_id = "PPY041"
    title   = "dict | operator requires PyPy 7.3.7+ (Python 3.9 compat)"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
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
                            "The dict | merge operator requires PyPy 7.3.7+ "
                            "(Python 3.9 compatibility level). On older PyPy "
                            "versions this raises TypeError. Always verify "
                            "the PyPy version when using Python 3.9+ features."
                        ),
                        severity=Severity.INFO,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Check PyPy version with sys.pypy_version_info "
                            "if targeting older PyPy releases. "
                            "Use {**d1, **d2} as a safer cross-version alternative."
                        ),
                        docs_url="https://peps.python.org/pep-0584/",
                    ))
        return findings