"""
CPY033 — pathlib.Path.is_relative_to requires Python 3.9+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pathlib.Path.is_relative_to() was added in Python 3.9.
Calling it on Python 3.8 or below raises AttributeError.
"""
from __future__ import annotations

import ast

from pyrift.analysis.constraints import eval_condition
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig
from pyrift.versions import Interval, Ver, VersionFacts

# The rule is irrelevant when the entire supported version range is
# already >= 3.9, expressed as a reusable constraint condition.
_REQUIRES_39: dict = {"type": "version_gte", "ver": Ver(3, 9)}


class IsRelativeToRule(BaseRule):
    rule_id = "CPY033"
    title   = "pathlib.Path.is_relative_to() requires Python 3.9+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        # Early-exit: if the project's minimum supported version is already
        # >= 3.9, is_relative_to() is always available and this rule cannot
        # fire.  We express this via eval_condition so the constraint logic
        # is centralised and testable independently of the rule.
        if target_config is not None and target_config.minimum is not None:
            facts = VersionFacts(
                runtime="cpython",
                interval=Interval(
                    lo=Ver(target_config.minimum.major, target_config.minimum.minor)
                ),
            )
            if eval_condition(_REQUIRES_39, facts):
                return []

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
                    func.attr == "is_relative_to"):
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