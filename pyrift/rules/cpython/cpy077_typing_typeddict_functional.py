"""
CPY077 — typing.TypedDict deprecated functional creation in 3.13, removed in 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.13 deprecated the functional syntax for typing.TypedDict:
  Point = TypedDict('Point', {'x': int, 'y': int})
  Point = TypedDict('Point', x=int, y=int)

This will be removed in Python 3.15. Use class-based syntax instead.

Detects:
  TypedDict('Name', {'key': type})
  TypedDict('Name', key=type)
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypingTypedDictFunctionalRule(BaseRule):
    rule_id = "CPY077"
    title   = "typing.TypedDict functional syntax deprecated in 3.13, removed in 3.15"
    runtime = "cpython"

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
            # TypedDict(...) or typing.TypedDict(...)
            is_typeddict = False
            if isinstance(func, ast.Name) and func.id == "TypedDict" or (isinstance(func, ast.Attribute)
                  and func.attr == "TypedDict"
                  and isinstance(func.value, ast.Name)
                  and func.value.id == "typing"):
                is_typeddict = True

            if not is_typeddict:
                continue

            # Must have name as first arg
            if len(n.args) < 1:
                continue

            # Check for dict literal: TypedDict('Name', {'x': int})
            has_dict_arg = (
                len(n.args) >= 2
                and isinstance(n.args[1], ast.Dict)
            )

            # Check for keyword args: TypedDict('Name', x=int)
            has_keyword_fields = any(
                kw.arg is not None and isinstance(kw.value, ast.Name)
                for kw in n.keywords
            )

            if has_dict_arg or has_keyword_fields:
                findings.append(Finding(
                    file=filename, line=n.lineno, col=n.col_offset,
                    rule_id=self.rule_id, title=self.title,
                    description=(
                        "typing.TypedDict() with functional syntax is deprecated "
                        "since Python 3.13 and will be removed in Python 3.15. "
                        "The functional form was rarely used and hard to read."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    affected_until="3.14",
                    suggestion=(
                        "Convert to class-based syntax:\n"
                        "  class Point(TypedDict):\n"
                        "      x: int\n"
                        "      y: int"
                    ),
                    docs_url="https://docs.python.org/3/whatsnew/3.13.html",
                ))
        return findings
