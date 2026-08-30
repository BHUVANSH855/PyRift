"""
CPY077 -- typing.TypedDict zero-field functional syntax removed in Python 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The zero-field and None-field functional syntax for TypedDict was removed
in Python 3.15. The following forms are no longer valid:

    TypedDict("Name")           # removed in 3.15
    TypedDict("Name", None)     # removed in 3.15

The standard dict-based functional syntax remains valid:

    TypedDict("Name", {"x": int})  # still valid

And the class-based syntax remains valid:

    class Name(TypedDict):
        x: int
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TypingTypedDictFunctionalRule(BaseRule):
    rule_id = "CPY077"
    title = "typing.TypedDict zero-field syntax removed in Python 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(self, node: ast.AST, filename: str, target_config=None) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue

            func = n.func
            is_typeddict = isinstance(func, ast.Name) and func.id == "TypedDict" or (
                isinstance(func, ast.Attribute)
                and func.attr == "TypedDict"
                and isinstance(func.value, ast.Name)
                and func.value.id == "typing"
            )

            if not is_typeddict:
                continue

            # Only flag zero-field: TypedDict("Name") or TypedDict("Name", None)
            # The dict-based form TypedDict("Name", {"x": int}) is still valid.
            is_zero_field = len(n.args) < 2
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
                    "The zero-field TypedDict functional syntax "
                    "TypedDict('Name') and TypedDict('Name', None) "
                    "were removed in Python 3.15. "
                    "Use the class-based syntax or the dict form: "
                    "TypedDict('Name', {'x': int})."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.15",
                affected_until="3.16",
                suggestion=(
                    "class Name(TypedDict):\n"
                    "    x: int\n"
                    "or: TypedDict('Name', {'x': int})"
                ),
                docs_url=(
                    "https://docs.python.org/3/library/typing.html"
                    "#typing.TypedDict"
                ),
            ))

        return findings