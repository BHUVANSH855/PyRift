"""
CPY098 -- calendar.January / calendar.February deprecated in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``calendar`` module previously exported ``calendar.January`` (= 1) and
``calendar.February`` (= 2) as numeric month constants.  In Python 3.13 these
were deprecated in favour of the new ``calendar.JANUARY`` and
``calendar.FEBRUARY`` aliases that follow the existing ``calendar.MONDAY``
naming convention.

Using the old names still works in 3.13 but raises ``DeprecationWarning``.

Reference: https://docs.python.org/3/whatsnew/3.13.html#deprecated
CPython issue: https://github.com/python/cpython/issues/105829
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_DEPRECATED = {
    "January": "JANUARY",
    "February": "FEBRUARY",
}


class CalendarDeprecatedConstantsRule(BaseRule):
    rule_id = "CPY098"
    title = "calendar.January / calendar.February deprecated in Python 3.13"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if (
                isinstance(n, ast.Attribute)
                and n.attr in _DEPRECATED
                and isinstance(n.value, ast.Name)
                and n.value.id == "calendar"
            ):
                new_name = _DEPRECATED[n.attr]
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"calendar.{n.attr} is deprecated since Python 3.13 "
                        "and raises DeprecationWarning. Use the uppercase "
                        f"calendar.{new_name} instead."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        f"Replace calendar.{n.attr} with calendar.{new_name}."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/whatsnew/3.13.html#deprecated"
                    ),
                    whatsnew_ref="3.13#deprecated",
                ))
        return findings
