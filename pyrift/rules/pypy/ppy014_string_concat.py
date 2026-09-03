"""
PPY014 — Repeated string concatenation in loops is O(n²) on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Repeated string concatenation in loops can have different performance
characteristics between CPython and PyPy.

This rule intentionally reports only augmented string concatenation
where the target can be identified as a string through static analysis.

String-type evidence is tracked per lexical scope so an assignment in
one function cannot incorrectly classify a same-named variable in an
unrelated function.

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
    severity = Severity.WARNING

    _SCOPE_TYPES = (
        ast.Module,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
    )

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
    def _scope_statements(cls, node: ast.AST) -> list[ast.stmt]:
        """Return statements belonging directly to one lexical scope."""
        if isinstance(
            node,
            (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            return list(node.body)

        return []

    @classmethod
    def _collect_string_names(cls, node: ast.AST) -> set[str]:
        """
        Collect string names belonging to a single lexical scope.

        Nested function, async-function, class, lambda, and comprehension
        scopes are intentionally excluded so names do not leak between
        unrelated scopes.
        """
        string_names: set[str] = set()

        def visit(current: ast.AST) -> None:
            if isinstance(
                current,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                return

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

            for child in ast.iter_child_nodes(current):
                visit(child)

        for statement in cls._scope_statements(node):
            visit(statement)

        return string_names

    @classmethod
    def _iter_lexical_scopes(cls, node: ast.AST) -> list[ast.AST]:
        """Return all lexical scopes reachable from *node*."""
        scopes: list[ast.AST] = []

        for current in ast.walk(node):
            if isinstance(current, cls._SCOPE_TYPES):
                scopes.append(current)

        return scopes

    @classmethod
    def _iter_loops_in_scope(
        cls,
        scope: ast.AST,
    ) -> list[ast.For | ast.While]:
        """
        Return loops belonging to one lexical scope.

        Nested function/class/lambda/comprehension scopes are skipped, but
        nested For/While loops remain part of the same lexical scope.
        """
        loops: list[ast.For | ast.While] = []

        def visit(current: ast.AST) -> None:
            if current is not scope and isinstance(
                current,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                return

            if isinstance(current, (ast.For, ast.While)):
                loops.append(current)

            for child in ast.iter_child_nodes(current):
                visit(child)

        for statement in cls._scope_statements(scope):
            visit(statement)

        return loops

    @classmethod
    def _is_string_target(
        cls,
        target: ast.AST,
        string_names: set[str],
    ) -> bool:
        """Return True when an augmented-assignment target is a string."""
        return isinstance(target, ast.Name) and target.id in string_names

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

        def visit(current: ast.AST) -> None:
            if isinstance(
                current,
                (
                    ast.For,
                    ast.While,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                    ast.ListComp,
                    ast.SetComp,
                    ast.DictComp,
                    ast.GeneratorExp,
                ),
            ):
                return

            if isinstance(current, ast.AugAssign):
                if (
                    isinstance(current.op, ast.Add)
                    and cls._is_string_target(current.target, string_names)
                ):
                    findings.append(current)
                return

            for child in ast.iter_child_nodes(current):
                visit(child)

        for statement in loop.body:
            visit(statement)

        return findings

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        reported_lines: set[tuple[int, int]] = set()

        for scope in self._iter_lexical_scopes(node):
            string_names = self._collect_string_names(scope)

            for loop in self._iter_loops_in_scope(scope):
                for concat in self._find_string_concats(
                    loop,
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