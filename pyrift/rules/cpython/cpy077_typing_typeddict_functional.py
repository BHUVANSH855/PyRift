"""
CPY077 — typing.TypedDict zero/None-field functional syntax deprecated 3.13, removed 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Two degenerate forms of the TypedDict functional syntax were deprecated in
Python 3.13 and disallowed (removed) in Python 3.15 (gh-133823):

    TD = TypedDict("TD")           # zero-field — no fields argument at all
    TD = TypedDict("TD", None)     # None-field — explicit None for fields

Both forms were always a source of confusion; they made it impossible to tell
at a glance whether the dict has zero keys by design or by accident.

Still valid after 3.15:
    class TD(TypedDict): pass          # class-based, zero-field
    TD = TypedDict("TD", {})           # dict-based, zero-field
    TD = TypedDict("TD", {"x": int})   # dict-based with fields

NOTE: The keyword-argument form ``TypedDict("TD", x=int)`` was a separate
deprecation (3.11→3.13) and is already hard-removed in 3.13; that is NOT
what this rule detects.

References:
  gh-105570  https://github.com/python/cpython/issues/105570
  What's New 3.13 (deprecated): https://docs.python.org/3/whatsnew/3.13.html#deprecated
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypingTypedDictFunctionalRule(BaseRule):
    rule_id = "CPY077"
    title   = "typing.TypedDict zero/None-field syntax deprecated 3.13, removed 3.15"
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
            is_typeddict = (
                (isinstance(func, ast.Name) and func.id == "TypedDict")
                or (
                    isinstance(func, ast.Attribute)
                    and func.attr == "TypedDict"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "typing"
                )
            )

            if not is_typeddict:
                continue

            # Keyword-argument form (TypedDict("TD", x=int)) was a separate
            # deprecation (3.11→3.13) and is already hard-removed in 3.13.
            # Do not double-flag it here.
            if n.keywords:
                continue

            # Zero-field: TypedDict("Name")  — name arg only, no fields arg
            is_zero_field = len(n.args) == 1

            # None-field: TypedDict("Name", None)
            is_none_field = (
                len(n.args) >= 2
                and isinstance(n.args[1], ast.Constant)
                and n.args[1].value is None
            )

            if not (is_zero_field or is_none_field):
                continue

            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "TypedDict('Name') and TypedDict('Name', None) were "
                    "deprecated in Python 3.13 and removed in "
                    "Python 3.15 (gh-133823). These zero/None-field forms are ambiguous; "
                    "use an explicit empty dict or the class syntax instead."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.13",
                affected_until="",
                suggestion=(
                    "Use the class-based syntax for a zero-field TypedDict: "
                    "'class Name(TypedDict): pass'. "
                    "Or use the explicit empty-dict functional form: "
                    "Name = TypedDict('Name', {}). "
                    "To add fields: Name = TypedDict('Name', {'x': int, 'y': str})."
                ),
                docs_url="https://docs.python.org/3/whatsnew/3.15.html#removed",
            ))

        return findings