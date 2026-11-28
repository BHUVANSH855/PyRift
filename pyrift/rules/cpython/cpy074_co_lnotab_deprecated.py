"""
CPY074 — code.co_lnotab deprecated in Python 3.10 (PEP 626), removed in 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PEP 626 (Python 3.10) deprecated code.co_lnotab in favour of the new
code.co_lines() method. A formal DeprecationWarning was added in 3.12
(gh-101866). The attribute was removed in Python 3.15 (gh-134690).

co_lnotab used a compact byte-pair encoding that could not represent line
numbers accurately (no line ranges, no negative deltas > 127). It raised
DeprecationWarning on 3.12–3.14 and raises AttributeError on 3.15+.

Replacements (all available since 3.10):
  code.co_lines()       → iterator of (start, end, lineno) tuples
  code.co_linetable     → raw location table bytes
  code.co_positions()   → iterator of (line, end_line, col, end_col) tuples

Detects:
  code_obj.co_lnotab      # any attribute access named co_lnotab
  code_obj.__lnotab__     # dunder alias used in some inspectors / tools
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class CoLnotabDeprecatedRule(BaseRule):
    rule_id = "CPY074"
    title   = "code.co_lnotab deprecated 3.10 (PEP 626), removed in 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        _LNOTAB_ATTRS = frozenset({"co_lnotab", "__lnotab__"})
        for n in ast.walk(node):
            if isinstance(n, ast.Attribute) and n.attr in _LNOTAB_ATTRS:
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "code.co_lnotab was deprecated in Python 3.10 (PEP 626) "
                        "and removed in Python 3.15 (gh-134690). "
                        "A formal DeprecationWarning was added in Python 3.12. "
                        "It used an inaccurate byte-pair encoding that cannot "
                        "represent line number ranges or column information."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.10",
                    affected_until="",
                    suggestion=(
                        "Use code.co_lines() (returns an iterator of "
                        "(start, end, lineno) tuples, available since 3.10) "
                        "or code.co_positions() (also includes column ranges, "
                        "available since 3.11) instead of code.co_lnotab."
                    ),
                    docs_url="https://docs.python.org/3/whatsnew/3.10.html#pep-626-precise-line-numbers-for-debugging-and-other-tools",
                ))
        return findings