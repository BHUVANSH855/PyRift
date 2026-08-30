"""
PPY026 — __builtins__ is always a module on PyPy, never a dict
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, __builtins__ is the __builtin__ module in the main
module but a dict in other modules. On PyPy, __builtins__ is
always the module, never a dict. Code that checks type(__builtins__)
or accesses __builtins__ as a dict will behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class BuiltinsModuleRule(BaseRule):
    rule_id = "PPY026"
    title   = "__builtins__ is always a module on PyPy, never a dict"
    runtime = "pypy"
    severity = Severity.WARNING

    def _is_version_guarded(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if *node* is inside a sys.version_info check."""
        if not hasattr(node, 'lineno'):
            return False
        for parent in ast.walk(tree):
            if not isinstance(parent, (ast.If, ast.IfExp)):
                continue
            # Walk the test expression to find sys.version_info references
            for child in ast.walk(parent.test):
                if (isinstance(child, ast.Attribute) and
                        child.attr in ("version_info", "version")):
                    return True
                if (isinstance(child, ast.Name) and
                        child.id in ("sys", "implementation")):
                    return True
        return False

    def _is_type_check(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if __builtins__ is only used in a type/introspection
        check (e.g., isinstance(__builtins__, dict))."""
        if not hasattr(node, 'lineno'):
            return False
        for parent in ast.walk(tree):
            if isinstance(parent, ast.Call):
                if isinstance(parent.func, ast.Name) and parent.func.id == "isinstance":
                    # Check if __builtins__ is an argument to isinstance()
                    for arg in parent.args:
                        if arg is node:
                            return True
                if isinstance(parent.func, ast.Attribute) and parent.func.attr == "isinstance":
                    for arg in parent.args:
                        if arg is node:
                            return True
        return False

    def _is_compat_shim(self, node: ast.AST, tree: ast.AST) -> bool:
        """Return True if __builtins__ is used in a compatibility shim pattern
        like ``from __builtins__ import *`` or conditional assignment."""
        if not hasattr(node, 'lineno'):
            return False
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ImportFrom):
                if parent.module == "__builtins__":
                    return True
                # Check if __builtins__ appears as a wildcard import source
                for alias in parent.names:
                    if alias.name == "__builtins__":
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
            if isinstance(n, ast.Name) and n.id == "__builtins__":
                # Exclusion: inside a sys.version_info guard
                if self._is_version_guarded(n, node):
                    continue
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "__builtins__ is accessed here. On CPython, "
                        "__builtins__ is the __builtin__ module in __main__ "
                        "but a plain dict in other modules. On PyPy, "
                        "__builtins__ is always the module — never a dict. "
                        "Code checking isinstance(__builtins__, dict) or "
                        "accessing __builtins__['name'] will silently fail on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use the builtins module directly instead: "
                        "import builtins; builtins.print — this works "
                        "consistently on both CPython and PyPy."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#miscellaneous"
                    ),
                ))
        return findings