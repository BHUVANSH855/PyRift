"""
PPY031 — Integer identity (is) can differ between CPython and PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Identity comparisons involving integers can behave differently between
CPython and PyPy.

This rule intentionally reports only comparisons where at least one
operand is statically recognizable as an integer value or integer
expression.

It does not report ordinary object identity checks such as:

    obj1 is obj2
    value is None
    value is True
    value is False
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class IntegerIdentityRule(BaseRule):
    rule_id = "PPY031"
    title = "Integer 'is' identity semantics differ on PyPy"
    runtime = "pypy"

    @staticmethod
    def _looks_like_integer(node: ast.AST) -> bool:
        """
        Return True when the AST node is statically recognizable as an
        integer value or integer expression.

        This intentionally favors precision over recall. Unknown names
        and arbitrary expressions are not treated as integers because
        doing so would produce false positives for ordinary identity
        comparisons.
        """
        if isinstance(node, ast.Constant):
            return (
                isinstance(node.value, int)
                and not isinstance(node.value, bool)
            )

        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
                return IntegerIdentityRule._looks_like_integer(
                    node.operand
                )

        if isinstance(node, ast.BinOp) and isinstance(
            node.op,
            (
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.FloorDiv,
                ast.Mod,
                ast.Pow,
                ast.LShift,
                ast.RShift,
                ast.BitAnd,
                ast.BitOr,
                ast.BitXor,
            ),
        ):
            return (
                IntegerIdentityRule._looks_like_integer(node.left)
                and IntegerIdentityRule._looks_like_integer(node.right)
            )

        return False

    @staticmethod
    def _is_exempt_identity_operand(node: ast.AST) -> bool:
        """
        Return True for identity operands where ``is`` is idiomatic and
        should not be reported.
        """
        return (
            isinstance(node, ast.Constant)
            and (
                node.value is None
                or node.value is True
                or node.value is False
            )
        )

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Compare):
                continue

            for index, op in enumerate(n.ops):
                if not isinstance(op, (ast.Is, ast.IsNot)):
                    continue

                left = n.left if index == 0 else n.comparators[index - 1]
                right = n.comparators[index]

                if (
                    self._is_exempt_identity_operand(left)
                    or self._is_exempt_identity_operand(right)
                ):
                    continue

                if not (
                    self._looks_like_integer(left)
                    or self._looks_like_integer(right)
                ):
                    continue

                findings.append(
                    Finding(
                        file=filename,
                        line=n.lineno,
                        col=n.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            "An identity comparison involves an integer "
                            "literal or integer expression. CPython and "
                            "PyPy can differ in integer object identity, "
                            "so using 'is' or 'is not' for integer value "
                            "comparison can produce different results "
                            "between runtimes."
                        ),
                        severity=Severity.WARNING,
                        runtime=Runtime.PYPY,
                        suggestion=(
                            "Use '==' or '!=' for integer value equality. "
                            "Reserve 'is' and 'is not' for object identity "
                            "checks such as None, True, False, or explicit "
                            "sentinel objects."
                        ),
                        docs_url=(
                            "https://doc.pypy.org/en/latest/"
                            "cpython_differences.html"
                            "#object-identity-of-primitive-values-is-and-id"
                        ),
                    )
                )

                break

        return findings
