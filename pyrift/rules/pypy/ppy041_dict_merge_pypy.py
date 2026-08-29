"""
PPY041 — dict | operator available on PyPy 7.3.7+ only
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The dict | merge operator (PEP 584) requires PyPy 7.3.7+
(which corresponds to CPython 3.9 compatibility).

This rule intentionally reports only expressions where the operands
can be identified as dictionaries. It does not treat every ``Name``
used with ``|`` as a dictionary because ``|`` is also valid for sets,
integers, and user-defined objects.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class DictMergePypyRule(BaseRule):
    rule_id = "PPY041"
    title = "dict | operator requires PyPy 7.3.7+ (Python 3.9 compat)"
    runtime = "pypy"

    @staticmethod
    def _is_dict_constructor(node: ast.AST) -> bool:
        """Return True when the node is a direct dict construction."""
        if isinstance(node, ast.Dict):
            return True

        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "dict"
        )

    @staticmethod
    def _is_dict_annotation(node: ast.AST) -> bool:
        """Return True when an annotation explicitly identifies a dict."""
        if isinstance(node, ast.Name):
            return node.id == "dict"

        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            return node.value.id == "dict"

        if isinstance(node, ast.Attribute):
            return node.attr == "dict"

        return False

    @classmethod
    def _collect_dict_names(cls, node: ast.AST) -> set[str]:
        """
        Collect names that have clear static evidence of being dicts.

        We deliberately avoid treating arbitrary names as dictionaries.
        """
        dict_names: set[str] = set()

        for current in ast.walk(node):
            if isinstance(current, ast.Assign):
                if cls._is_dict_constructor(current.value):
                    for target in current.targets:
                        if isinstance(target, ast.Name):
                            dict_names.add(target.id)

            elif isinstance(current, ast.AnnAssign):
                if (
                    isinstance(current.target, ast.Name)
                    and cls._is_dict_annotation(current.annotation)
                ):
                    dict_names.add(current.target.id)

                if (
                    isinstance(current.target, ast.Name)
                    and current.value is not None
                    and cls._is_dict_constructor(current.value)
                ):
                    dict_names.add(current.target.id)

        return dict_names

    @classmethod
    def _is_dict_operand(
        cls,
        node: ast.AST,
        dict_names: set[str],
    ) -> bool:
        """Return True when the operand is statically dict-like."""
        if cls._is_dict_constructor(node):
            return True

        return (
            isinstance(node, ast.Name)
            and node.id in dict_names
        )

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        dict_names = self._collect_dict_names(node)

        for current in ast.walk(node):
            if not isinstance(current, ast.BinOp):
                continue

            if not isinstance(current.op, ast.BitOr):
                continue

            left_is_dict = self._is_dict_operand(
                current.left,
                dict_names,
            )
            right_is_dict = self._is_dict_operand(
                current.right,
                dict_names,
            )

            if not (left_is_dict and right_is_dict):
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=current.lineno,
                    col=current.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "The dict | merge operator requires PyPy 7.3.7+ "
                        "(Python 3.9 compatibility level). On older PyPy "
                        "versions this raises TypeError. The operands were "
                        "identified as dictionaries by static analysis."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Check PyPy version with sys.pypy_version_info "
                        "if targeting older PyPy releases. "
                        "Use {**d1, **d2} as a safer cross-version "
                        "alternative."
                    ),
                    docs_url="https://peps.python.org/pep-0584/",
                )
            )

        return findings