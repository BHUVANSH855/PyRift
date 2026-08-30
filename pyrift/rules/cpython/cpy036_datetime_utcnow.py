"""
CPY036 — datetime.datetime.utcnow() deprecated in Python 3.12
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
datetime.datetime.utcnow() was deprecated in Python 3.12 because
it returns a naive datetime with no timezone info, making it easy
to confuse with local time. It will be removed in a future version.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DatetimeUtcnowRule(BaseRule):
    rule_id = "CPY036"
    title = "datetime.utcnow() deprecated since Python 3.12"
    runtime = "cpython"
    severity = Severity.WARNING

    @staticmethod
    def _datetime_module_names(node: ast.Module) -> set[str]:
        """Return names bound to the datetime module."""
        names: set[str] = set()

        for statement in node.body:
            if not isinstance(statement, ast.Import):
                continue

            for alias in statement.names:
                if alias.name == "datetime":
                    names.add(alias.asname or "datetime")

        return names

    @staticmethod
    def _is_datetime_utcnow_call(
        call: ast.Call,
        datetime_names: set[str],
    ) -> bool:
        func = call.func

        if not isinstance(func, ast.Attribute):
            return False

        if func.attr != "utcnow":
            return False

        receiver = func.value

        return (
            isinstance(receiver, ast.Attribute)
            and receiver.attr == "datetime"
            and isinstance(receiver.value, ast.Name)
            and (
                receiver.value.id in datetime_names
                or receiver.value.id == "datetime"
            )
        )

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if not isinstance(node, ast.Module):
            return []

        datetime_names = self._datetime_module_names(node)
        findings: list[Finding] = []

        for current in ast.walk(node):
            if not isinstance(current, ast.Call):
                continue

            if not self._is_datetime_utcnow_call(
                current,
                datetime_names,
            ):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=current.lineno,
                    col=current.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "datetime.datetime.utcnow() is deprecated since "
                        "Python 3.12. It returns a naive datetime object "
                        "with no timezone information, making it dangerously "
                        "easy to confuse with local time. It will be removed "
                        "in a future Python version."
                    ),
                    severity=self.severity,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.12",
                    suggestion=(
                        "Use datetime.datetime.now(datetime.timezone.utc) "
                        "which returns a timezone-aware UTC datetime. "
                        "Or with Python 3.11+: datetime.datetime.now(datetime.UTC)"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/datetime.html"
                        "#datetime.datetime.utcnow"
                    ),
                )
            )

        return findings