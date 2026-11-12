"""
CPY035 — str.removeprefix / str.removesuffix require Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
str.removeprefix() and str.removesuffix() were added in Python 3.9
(PEP 616). Calling them on Python 3.8 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

STR_METHODS_39 = {"removeprefix", "removesuffix"}


class RemovePrefixRule(BaseRule):
    rule_id = "CPY035"
    title   = "str.removeprefix/removesuffix requires Python 3.9+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        # --- O(n) pass 1: build guard index ---
        version_guarded_lines: set[int] = set()
        try_guarded_lines: set[int] = set()

        for parent in ast.walk(node):
            if isinstance(parent, (ast.If, ast.IfExp)):
                for child in ast.walk(parent.test):
                    is_version_guard = False
                    if isinstance(child, ast.Compare):
                        for comp in child.comparators:
                            if isinstance(comp, ast.Name) and comp.id == "version_info":
                                is_version_guard = True
                            if isinstance(comp, ast.Tuple):
                                for elt in comp.elts:
                                    if (isinstance(elt, ast.Constant)
                                            and isinstance(elt.value, int)
                                            and elt.value >= 9):
                                        is_version_guard = True
                    elif isinstance(child, ast.Attribute) and child.attr == "version_info":
                        is_version_guard = True
                    if is_version_guard:
                        for n in ast.walk(parent):
                            if hasattr(n, "lineno"):
                                version_guarded_lines.add(n.lineno)
                        break

            elif isinstance(parent, ast.Try):
                is_attr_guarded = False
                for handler in parent.handlers:
                    if handler.type is None or isinstance(handler.type, ast.Name) and handler.type.id == "AttributeError":
                        is_attr_guarded = True
                    elif isinstance(handler.type, ast.Tuple):
                        for elt in handler.type.elts:
                            if isinstance(elt, ast.Name) and elt.id == "AttributeError":
                                is_attr_guarded = True
                if is_attr_guarded:
                    for n in ast.walk(parent):
                        if hasattr(n, "lineno"):
                            try_guarded_lines.add(n.lineno)

        # --- O(n) pass 2: collect findings ---
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if (isinstance(func, ast.Attribute) and
                    func.attr in STR_METHODS_39):
                if n.lineno in version_guarded_lines:
                    continue
                if n.lineno in try_guarded_lines:
                    continue
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"str.{func.attr}() was added in Python 3.9 "
                        "(PEP 616). Calling it on Python 3.8 or below "
                        "raises AttributeError at runtime."
                    ),
                    severity=Severity.ERROR,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    affected_until="3.8",
                    suggestion=(
                        "For Python 3.8 compatibility: "
                        "s[len(prefix):] if s.startswith(prefix) else s "
                        "(for removeprefix) or "
                        "s[:-len(suffix)] if s.endswith(suffix) else s "
                        "(for removesuffix)."
                    ),
                    docs_url="https://peps.python.org/pep-0616/",
                ))
        return findings