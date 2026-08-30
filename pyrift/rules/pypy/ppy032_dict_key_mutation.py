"""
PPY032 — Mutating an object used as a dict key raises on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, mutating a mutable object while it is used as a dict
key (e.g. changing a set that is a dict key) may silently corrupt
the dict. On PyPy, this raises a RuntimeError immediately.
While PyPy is stricter here, code that mutates dict keys will
behave differently on each runtime.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DictKeyMutationRule(BaseRule):
    rule_id = "PPY032"
    title   = "Mutating dict keys raises RuntimeError on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # Detect dict literals with mutable keys (set literals)
            if not isinstance(n, ast.Dict):
                continue
            for key in n.keys:
                if key is None:
                    continue
                # set literal as dict key — always wrong but detected
                if isinstance(key, ast.Set):
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "A mutable object is used as a dict key. "
                            "On PyPy, mutating an object while it is used "
                            "as a dict key immediately raises RuntimeError. "
                            "On CPython, the same operation may silently "
                            "corrupt the dict without raising an error."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Use immutable objects as dict keys — "
                            "frozenset instead of set, tuple instead of list. "
                            "Never mutate an object that is used as a dict key."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/cpython_differences.html"
                            "#mutating-classes-of-objects-which-are-already-used"
                            "-as-dictionary-keys"
                        ),
                    ))
        return findings