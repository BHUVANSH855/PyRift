"""
CPY095 -- argparse.BooleanOptionalAction no longer accepts type/choices/metavar
           in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ``argparse.BooleanOptionalAction`` action accepted (but silently ignored)
the ``type``, ``choices``, and ``metavar`` keyword arguments when passed to
``add_argument()``.  In Python 3.14 these arguments are removed: passing them
now raises ``ValueError``.

Deprecated since: 3.12
Removed in: 3.14 (gh-118805)

Reference: https://docs.python.org/3/whatsnew/3.14.html#removed
CPython issue: https://github.com/python/cpython/issues/118805
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

_REMOVED_KWARGS = frozenset({"type", "choices", "metavar"})


def _uses_boolean_optional_action(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg == "action":
            value = kw.value
            if isinstance(value, ast.Constant) and value.value == "BooleanOptionalAction":
                return True
    return False


def _bad_kwargs_in_call(call: ast.Call) -> list[str]:
    return [
        kw.arg
        for kw in call.keywords
        if kw.arg in _REMOVED_KWARGS
    ]


class ArgparseBooleanOptionalRemovedRule(BaseRule):
    rule_id = "CPY095"
    title = "argparse.BooleanOptionalAction: type/choices/metavar removed in Python 3.14"
    runtime = "cpython"
    severity = Severity.ERROR

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
            is_add_argument = (
                isinstance(func, ast.Attribute)
                and func.attr == "add_argument"
            ) or (
                isinstance(func, ast.Name)
                and func.id == "add_argument"
            )
            if not is_add_argument:
                continue
            if not _uses_boolean_optional_action(n):
                continue
            bad = _bad_kwargs_in_call(n)
            if not bad:
                continue
            kwlist = ", ".join(repr(k) for k in bad)
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"add_argument() with action='BooleanOptionalAction' "
                    f"no longer accepts the {kwlist} keyword argument(s) "
                    "in Python 3.14. These were deprecated since 3.12 and "
                    "now raise ValueError."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.14",
                suggestion=(
                    f"Remove the {kwlist} keyword argument(s) from "
                    "this add_argument() call. "
                    "BooleanOptionalAction generates --flag / --no-flag "
                    "pairs and does not require type, choices, or metavar."
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.14.html#removed"
                ),
                whatsnew_ref="3.14#removed",
            ))
        return findings
