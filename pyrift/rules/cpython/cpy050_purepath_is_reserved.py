"""
CPY050 — PurePath.is_reserved() deprecated in Python 3.13
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pathlib.PurePath.is_reserved() was deprecated in Python 3.13
and will be removed in Python 3.15. On Windows, use
os.path.isreserved() instead. On other platforms, the method
always returned False anyway.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class PurePathIsReservedRule(BaseRule):
    rule_id = "CPY050"
    title = "PurePath.is_reserved() deprecated in 3.13, removed in 3.15"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        pathlib_aliases: set[str] = {"pathlib"}
        purepath_names: set[str] = {"PurePath"}
        purepath_instances: set[str] = set()

        for statement in node.body if isinstance(node, ast.Module) else []:
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    if alias.name == "pathlib":
                        pathlib_aliases.add(alias.asname or "pathlib")

            elif (
                isinstance(statement, ast.ImportFrom)
                and statement.module == "pathlib"
            ):
                for alias in statement.names:
                    if alias.name == "PurePath":
                        purepath_names.add(alias.asname or "PurePath")

        for statement in ast.walk(node):  # type: ignore[assignment]
            if not isinstance(statement, ast.Assign):
                continue

            if not isinstance(statement.value, ast.Call):
                continue

            call = statement.value
            is_purepath_constructor = False

            if isinstance(call.func, ast.Name):
                is_purepath_constructor = call.func.id in purepath_names

            elif isinstance(call.func, ast.Attribute):
                is_purepath_constructor = (
                    isinstance(call.func.value, ast.Name)
                    and call.func.value.id in pathlib_aliases
                    and call.func.attr == "PurePath"
                )

            if not is_purepath_constructor:
                continue

            for target in statement.targets:
                if isinstance(target, ast.Name):
                    purepath_instances.add(target.id)

        for statement in ast.walk(node):  # type: ignore[assignment]
            if not isinstance(statement, ast.Call):
                continue

            func = statement.func

            if not isinstance(func, ast.Attribute):
                continue

            if func.attr != "is_reserved":
                continue

            if not (
                isinstance(func.value, ast.Name)
                and func.value.id in purepath_instances
            ):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=statement.lineno,
                    col=statement.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "pathlib.PurePath.is_reserved() was deprecated in "
                        "Python 3.13 and will be removed in Python 3.15. "
                        "On non-Windows platforms it always returned False. "
                        "On Windows, use os.path.isreserved() instead."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.13",
                    suggestion=(
                        "Replace with: import os; os.path.isreserved(path) "
                        "for Windows reserved path detection. "
                        "This works on Python 3.13+ on all platforms."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/pathlib.html"
                    ),
                )
            )

        return findings