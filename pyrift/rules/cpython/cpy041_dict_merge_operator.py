"""
CPY041 — dict merge operator | requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The | operator for dict merging and |= for dict update were
added in Python 3.9 (PEP 584). Using them on 3.8 or below
raises TypeError at runtime.

Detection strategy:
- Flag d1 | d2 only when at least one operand is a dict literal {}
  (bare Name | Name is too broad — could be int, set, etc.)
- Flag d |= other only when the target looks like a dict variable
  (based on naming conventions), to avoid false positives on sets and ints.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _is_dict_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Dict)


def _looks_like_dict(node: ast.AST) -> bool:
    """True only for clear dict signals — literals or subscripts of known names."""
    return isinstance(node, ast.Dict)


_DICT_LIKE_NAMES = frozenset({
    "d", "data", "config", "options", "settings", "kwargs", "params",
    "attrs", "props", "state", "env", "ctx", "context", "table", "map",
    "mapping", "cache", "registry", "store", "db", "result", "output",
    "info", "meta", "metadata", "extra", "defaults", "overrides", "merged",
    "combined", "base", "patch", "updates", "changes", "diff", "delta",
    "new", "old", "src", "source", "target", "dest", "destination",
})


class DictMergeOperatorRule(BaseRule):
    rule_id = "CPY041"
    title   = "dict | merge operator requires Python 3.9+"
    runtime = "cpython"

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            # d1 | d2 — only flag when at least one side is a dict literal
            # Name | Name is too ambiguous (could be sets, ints, flags, etc.)
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
                left_is_dict = _looks_like_dict(n.left)
                right_is_dict = _looks_like_dict(n.right)
                if left_is_dict or right_is_dict:
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

            # d |= other — augmented assign; only flag dict-like names
            if (
                isinstance(n, ast.AugAssign)
                and isinstance(n.op, ast.BitOr)
                and isinstance(n.target, ast.Name)
                and n.target.id in _DICT_LIKE_NAMES
            ):
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