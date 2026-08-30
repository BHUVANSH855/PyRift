"""
CPY067 -- typing.NamedTuple keyword syntax removed in Python 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The undocumented keyword-argument form of NamedTuple was removed in 3.15:

    NamedTuple("Point", x=int, y=int)   # removed in 3.15

The standard functional forms remain valid:

    NamedTuple("Point", [("x", int), ("y", int)])  # valid
    NamedTuple("Point", {"x": int, "y": int})      # valid (2-arg dict form)

The class-based syntax remains valid:

    class Point(NamedTuple):
        x: int
        y: int
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class TypingNamedTupleKeywordRule(BaseRule):
    rule_id = "CPY067"
    title = "typing.NamedTuple keyword syntax removed in Python 3.15"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str, target_config=None) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue

            func = n.func
            is_namedtuple = isinstance(func, ast.Name) and func.id == "NamedTuple" or (
                isinstance(func, ast.Attribute)
                and func.attr == "NamedTuple"
                and isinstance(func.value, ast.Name)
                and func.value.id == "typing"
            )

            if not is_namedtuple:
                continue

            # Must have at least 1 arg (name)
            if len(n.args) < 1:
                continue

            # Only flag keyword-argument form: NamedTuple("Point", x=int, y=int)
            # The list and dict forms remain valid.
            has_keyword_fields = bool(n.keywords) and not any(
                kw.arg is None for kw in n.keywords  # exclude **kwargs
            )

            if not has_keyword_fields:
                continue

            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "The keyword-argument form of NamedTuple "
                    "NamedTuple('Point', x=int, y=int) was removed in "
                    "Python 3.15. Use the class syntax or list form."
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.15",
                suggestion=(
                    "class Point(NamedTuple):\\n"
                    "    x: int\\n"
                    "    y: int\\n"
                    "or: NamedTuple('Point', [('x', int), ('y', int)])"
                ),
                docs_url=(
                    "https://docs.python.org/3/library/typing.html"
                    "#typing.NamedTuple"
                ),
            ))

        return findings