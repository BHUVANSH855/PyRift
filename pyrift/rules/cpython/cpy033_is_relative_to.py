"""
CPY033 — pathlib.Path.is_relative_to requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pathlib.Path.is_relative_to() was added in Python 3.9.
Calling it on Python 3.8 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class IsRelativeToRule(BaseRule):
    rule_id = "CPY033"
    title   = "pathlib.Path.is_relative_to() requires Python 3.9+"
    runtime = "cpython"
    severity = Severity.ERROR

    def _is_version_guarded(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if *node* is inside a sys.version_info >= (3, 9) guard."""
        if not hasattr(node, 'lineno'):
            return False
        for parent in ast.walk(tree):
            if not isinstance(parent, (ast.If, ast.IfExp)):
                continue
            for child in ast.walk(parent.test):
                if (isinstance(child, ast.Compare)):
                    # Look for version_info >= (3, 9) or sys.version >= "3.9"
                    has_version = False
                    for comp in child.comparators:
                        if isinstance(comp, ast.Name) and comp.id == "version_info":
                            has_version = True
                        if isinstance(comp, ast.Tuple):
                            for elt in comp.elts:
                                if (isinstance(elt, ast.Constant)
                                        and isinstance(elt.value, int)
                                        and elt.value >= 9):
                                    has_version = True
                    if has_version:
                        return True
                if (isinstance(child, ast.Attribute) and
                        child.attr == "version_info"):
                    # Generic version_info check — assume guarded
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
            # Check if any handler catches AttributeError
            for handler in parent.handlers:
                if handler.type is None:
                    # bare except
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
                    func.attr == "is_relative_to"):
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
                        "pathlib.Path.is_relative_to() was added in "
                        "Python 3.9. Calling it on Python 3.8 or below "
                        "raises AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "For Python 3.8 compatibility use: "
                        "try: path.relative_to(base); return True "
                        "except ValueError: return False"
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/pathlib.html"
                        "#pathlib.PurePath.is_relative_to"
                    ),
                ))
        return findings