"""
CPY078 -- functools.reduce() keyword arguments deprecated, scheduled removal in 3.16
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calling the Python implementation of functools.reduce() with `function`
or `sequence` passed as keyword arguments (rather than positionally) is
deprecated since Python 3.14 and is on the "pending removal in 3.16"
list in the official Python documentation:
https://docs.python.org/3/deprecations/pending-removal-in-3.16.html

    functools.reduce(function=f, sequence=xs)          # deprecated
    functools.reduce(f, sequence=xs)                    # deprecated
    functools.reduce(f, xs)                              # fine
    functools.reduce(f, xs, initial)                     # fine

This is item #10/#100 of the 2026-09 architecture review's "next wave"
of Python 3.16 rules (CPY078+).
"""
from __future__ import annotations

import ast

from pyrift.analysis.calls import collect_calls
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class FunctoolsReduceKeywordArgsRule(BaseRule):
    rule_id = "CPY078"
    title = "functools.reduce() keyword arguments deprecated, removal scheduled for 3.16"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for call in collect_calls(node, "reduce", module="functools"):
            offending = sorted(
                name for name in ("function", "sequence") if name in call.kwargs
            )
            if not offending:
                continue

            findings.append(Finding(
                file=filename,
                line=call.line,
                col=call.col,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "Calling the Python implementation of "
                    "functools.reduce() with "
                    f"{' and '.join(offending)} passed as keyword "
                    "argument(s) is deprecated since Python 3.14 and "
                    "is scheduled for removal in Python 3.16. Pass "
                    "them positionally instead."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.CPYTHON,
                affected_from="3.14",
                affected_until="3.16",
                suggestion=(
                    "Call functools.reduce(function, sequence[, "
                    "initial]) positionally instead of using "
                    "function=/sequence= keyword arguments."
                ),
                docs_url=(
                    "https://docs.python.org/3/deprecations/"
                    "pending-removal-in-3.16.html"
                ),
            ))

        return findings
