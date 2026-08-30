"""
CPY067 — typing.NamedTuple keyword-only syntax deprecated in 3.13, removed in 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Python 3.13 deprecated the keyword argument syntax for typing.NamedTuple
in favor of the class-based syntax. Python 3.15 removes it entirely.

  # OLD (deprecated 3.13, removed 3.15):
  Point = typing.NamedTuple('Point', x=int, y=int)

  # NEW (preferred):
  class Point(typing.NamedTuple):
      x: int
      y: int

Detects the keyword argument form of typing.NamedTuple().
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypingNamedTupleKeywordRule(BaseRule):
    rule_id = "CPY067"
    title   = "typing.NamedTuple keyword syntax deprecated in 3.13, removed in 3.15"
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
            # typing.NamedTuple(...) or NamedTuple(...)
            is_namedtuple = False
            if isinstance(func, ast.Name) and func.id == "NamedTuple" or (isinstance(func, ast.Attribute)
                  and func.attr == "NamedTuple"
                  and isinstance(func.value, ast.Name)
                  and func.value.id == "typing"):
                is_namedtuple = True

            if not is_namedtuple:
                continue

            # Must have at least 1 arg (name)
            if len(n.args) < 1:
                continue

            # Check for keyword form: NamedTuple('Name', x=int, y=str)
            has_keyword_fields = any(
                kw.arg is not None and isinstance(kw.value, ast.Name)
                for kw in n.keywords
            )
            if has_keyword_fields:
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "typing.NamedTuple() with keyword arguments is deprecated "
                        "since Python 3.13 and will be removed in Python 3.15. "
                        "The functional form NamedTuple('Name', x=int) must be "
                        "replaced with the class-based syntax."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    affected_until="3.14",
                    suggestion=(
                        "Convert to class-based syntax:\n"
                        "  class Point(typing.NamedTuple):\n"
                        "      x: int\n"
                        "      y: int"
                    ),
                    docs_url="https://docs.python.org/3/whatsnew/3.13.html",
                ))

            # Check for dict form: NamedTuple('Name', {'x': int, 'y': str})
            if (len(n.args) >= 2
                    and isinstance(n.args[1], ast.Dict)
                    and not n.keywords):
                has_dict_type_values = any(
                    isinstance(v, ast.Name) for v in n.args[1].values
                )
                if has_dict_type_values:
                    findings.append(Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "typing.NamedTuple() with dict argument is deprecated "
                            "since Python 3.13 and will be removed in Python 3.15. "
                            "The functional form NamedTuple('Name', {'x': int}) "
                            "must be replaced with the class-based syntax."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.13",
                        affected_until="3.14",
                        suggestion=(
                            "Convert to class-based syntax:\n"
                            "  class Point(typing.NamedTuple):\n"
                            "      x: int\n"
                            "      y: int"
                        ),
                        docs_url="https://docs.python.org/3/whatsnew/3.13.html",
                    ))
        return findings
