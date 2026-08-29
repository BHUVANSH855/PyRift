"""
CPY034 — int.bit_count() requires Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
int.bit_count() was added in Python 3.10.
Calling it on Python 3.9 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class BitCountRule(BaseRule):
    rule_id = "CPY034"
    title   = "int.bit_count() requires Python 3.10+"
    runtime = "cpython"

    def _is_version_guarded(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if *node* is inside a sys.version_info >= (3, 10) guard."""
        if not hasattr(node, 'lineno'):
            return False
        for parent in ast.walk(tree):
            if not isinstance(parent, (ast.If, ast.IfExp)):
                continue
            for child in ast.walk(parent.test):
                if isinstance(child, ast.Compare):
                    has_version = False
                    for comp in child.comparators:
                        if isinstance(comp, ast.Name) and comp.id == "version_info":
                            has_version = True
                        if isinstance(comp, ast.Tuple):
                            for elt in comp.elts:
                                if (isinstance(elt, ast.Constant)
                                        and isinstance(elt.value, int)
                                        and elt.value >= 10):
                                    has_version = True
                    if has_version:
                        return True
                if (isinstance(child, ast.Attribute) and
                        child.attr == "version_info"):
                    return True
        return False

    def _is_try_except_guarded(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if *node* is inside a try block that catches
        AttributeError."""
        if not hasattr(node, 'lineno'):
            return False
        for parent in ast.walk(tree):
            if not isinstance(parent, ast.Try):
                continue
            for handler in parent.handlers:
                if handler.type is None:
                    return True
                if isinstance(handler.type, ast.Name) and handler.type.id == "AttributeError":
                    return True
                if isinstance(handler.type, ast.Tuple):
                    for elt in handler.type.elts:
                        if isinstance(elt, ast.Name) and elt.id == "AttributeError":
                            return True
        return False

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
            if (isinstance(func, ast.Attribute) and
                    func.attr == "bit_count"):
                # Exclusion: version guard or try/except
                if self._is_version_guarded(n, node):
                    continue
                if self._is_try_except_guarded(n, node):
                    continue
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "int.bit_count() was added in Python 3.10. "
                        "Calling it on Python 3.9 or below raises "
                        "AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.9",
                    suggestion=(
                        "For Python 3.9 compatibility use: "
                        "bin(n).count('1') "
                        "which works on all Python 3 versions."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/stdtypes.html"
                        "#int.bit_count"
                    ),
                ))
        return findings