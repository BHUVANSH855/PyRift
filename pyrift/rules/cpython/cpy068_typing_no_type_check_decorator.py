"""
CPY068 — typing.no_type_check_decorator removed in Python 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
typing.no_type_check_decorator was deprecated in Python 3.13 and will be
removed in Python 3.15. It was used to mark a decorator as suppressing
type-checking, but it was rarely used and inconsistently implemented.

Detects:
  from typing import no_type_check_decorator
  @typing.no_type_check_decorator
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class TypingNoTypeCheckDecoratorRule(BaseRule):
    rule_id = "CPY068"
    title   = "typing.no_type_check_decorator deprecated in 3.13, removed in 3.15"
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
            # from typing import no_type_check_decorator
            if isinstance(n, ast.ImportFrom) and n.module == "typing":
                for alias in n.names:
                    if alias.name == "no_type_check_decorator":
                        findings.append(Finding(
                            file=filename, line=n.lineno, col=n.col_offset,
                            rule_id=self.rule_id, title=self.title,
                            description=(
                                "typing.no_type_check_decorator was deprecated "
                                "in Python 3.13 and will be removed in Python 3.15. "
                                "It was rarely used and inconsistently implemented."
                            ),
                            severity=Severity.WARNING,
                            runtime=Runtime.CPYTHON,
                            affected_from="3.13",
                            affected_until="3.15",
                            suggestion=(
                                "Use typing.no_type_check() as a function decorator "
                                "or use typing.TYPE_CHECKING with if-blocks instead."
                            ),
                            docs_url="https://docs.python.org/3/whatsnew/3.13.html",
                        ))

            # @typing.no_type_check_decorator usage
            if (isinstance(n, ast.Attribute)
                    and n.attr == "no_type_check_decorator"
                    and isinstance(n.value, ast.Name)
                    and n.value.id == "typing"):
                findings.append(Finding(
                        file=filename, line=n.lineno, col=n.col_offset,
                        rule_id=self.rule_id, title=self.title,
                        description=(
                            "typing.no_type_check_decorator was deprecated "
                            "in Python 3.13 and will be removed in Python 3.15."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.13",
                        affected_until="3.14",
                        suggestion=(
                            "Use typing.no_type_check() as a function decorator."
                        ),
                        docs_url="https://docs.python.org/3/whatsnew/3.13.html",
                    ))

        # Deduplicate
        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []
        for f in findings:
            key = (f.line, f.col)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
