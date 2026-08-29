"""
PPY014 — Repeated string concatenation in loops is O(n²) on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Repeated string concatenation in loops can have different performance
characteristics between CPython and PyPy.

This rule intentionally reports only augmented string concatenation
where the target can be identified as a string through static analysis.

It does not report arbitrary ``+=`` operations on unknown variables,
integers, lists, or other objects.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class StringConcatLoopRule(BaseRule):
    rule_id = "PPY014"
    title = "String concatenation in loop is O(n²) on PyPy"
    runtime = "pypy"

    @staticmethod
    def _is_string_value(node: ast.AST | None) -> bool:
        """Return True when the expression is statically string-like."""
        if node is None:
            return False

        if isinstance(node, ast.Constant):
            return isinstance(node.value, str)

        if isinstance(node, ast.JoinedStr):
            return True

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return (
                StringConcatLoopRule._is_string_value(node.left)
                or StringConcatLoopRule._is_string_value(node.right)
            )

        if isinstance(node, ast.Call):
            return (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "join"
            )

        return False

    @staticmethod
    def _is_string_annotation(node: ast.AST) -> bool:
        """Return True when an annotation explicitly identifies str."""
        if isinstance(node, ast.Name):
            return node.id == "str"

        if isinstance(node, ast.Attribute):
            return node.attr == "str"

        return False

    @classmethod
    def _collect_string_names(cls, node: ast.AST) -> set[str]:
        """
        Collect names that have clear static evidence of being strings.

        Unknown variables are intentionally excluded to avoid false
        positives.
        """
        string_names: set[str] = set()

        for current in ast.walk(node):
            if isinstance(current, ast.Assign):
                if cls._is_string_value(current.value):
                    for target in current.targets:
                        if isinstance(target, ast.Name):
                            string_names.add(target.id)

            elif isinstance(current, ast.AnnAssign):
                if (
                    isinstance(current.target, ast.Name)
                    and cls._is_string_annotation(current.annotation)
                ):
                    string_names.add(current.target.id)

                if (
                    isinstance(current.target, ast.Name)
                    and cls._is_string_value(current.value)
                ):
                    string_names.add(current.target.id)

        return string_names

    @classmethod
    def _is_string_target(
        cls,
        target: ast.AST,
        string_names: set[str],
    ) -> bool:
        """Return True when an augmented-assignment target is a string."""
        return (
            isinstance(target, ast.Name)
            and target.id in string_names
        )

    @classmethod
    def _find_string_concats(
        cls,
        loop: ast.For | ast.While,
        string_names: set[str],
    ) -> list[ast.AugAssign]:
        """
        Find string ``+=`` operations belonging directly to this loop.

        Nested loops are treated as separate loop scopes. Their bodies
        are not traversed here because the outer loop must not report
        concatenations that belong to an inner loop.
        """
        findings: list[ast.AugAssign] = []

        def visit(statements: list[ast.stmt]) -> None:
            for statement in statements:
                if isinstance(statement, (ast.For, ast.While)):
                    continue

                if isinstance(statement, ast.AugAssign):
                    if (
                        isinstance(statement.op, ast.Add)
                        and cls._is_string_target(
                            statement.target,
                            string_names,
                        )
                    ):
                        findings.append(statement)

                    continue

                for child in ast.iter_child_nodes(statement):
                    if isinstance(child, ast.stmt):
                        visit([child])
                    else:
                        for descendant in ast.iter_child_nodes(child):
                            if isinstance(descendant, ast.stmt):
                                visit([descendant])

        visit(loop.body)

        return findings

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        string_names = self._collect_string_names(node)

        reported_lines: set[tuple[int, int]] = set()

        for current in ast.walk(node):
            if not isinstance(current, (ast.For, ast.While)):
                continue

            for concat in self._find_string_concats(
                current,
                string_names,
            ):
                location = (
                    concat.lineno,
                    concat.col_offset,
                )

                if location in reported_lines:
                    continue

                reported_lines.add(location)

                target_name = (
                    concat.target.id
                    if isinstance(concat.target, ast.Name)
                    else ""
                )

                findings.append(
                    Finding(
                        file=filename,
                        line=concat.lineno,
                        col=concat.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"String variable '{target_name}' is "
                            "concatenated with += inside a loop. "
                            "Repeated string concatenation can have "
                            "different performance characteristics on "
                            "PyPy and may become O(n²) for large inputs."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Use a list and join at the end: "
                            "parts = []; parts.append(s); "
                            "result = ''.join(parts). "
                            "This avoids repeated string concatenation."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/"
                            "cpython_differences.html"
                            "#performance-differences"
                        ),
                    )
                )

        return findings