"""
CPY008 — __slots__ + __dict__ inheritance change in Python 3.10+
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In Python 3.10, the behaviour of classes that define __slots__ but
inherit from a class that has __dict__ changed subtly. Code relying
on __slots__ to prevent __dict__ creation silently fails on older
versions when a parent class has __dict__.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SlotsDictRule(BaseRule):
    rule_id = "CPY008"
    title   = "__slots__ may not prevent __dict__ on Python < 3.10"
    runtime = "cpython"
    severity = Severity.INFO

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.ClassDef):
                continue

            # Class must have __slots__
            has_slots = False
            for item in n.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if (isinstance(target, ast.Name) and
                                target.id == "__slots__"):
                            has_slots = True

            if not has_slots:
                continue

            # Class must have at least one base class (not just object)
            if not n.bases:
                continue

            # Flag if base is not just bare 'object'
            for base in n.bases:
                if isinstance(base, ast.Name) and base.id == "object":
                    continue
                # Has a non-trivial base + __slots__ — potential issue
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"Class '{n.name}' defines __slots__ but inherits "
                        "from a non-trivial base class. If any ancestor class "
                        "has __dict__, __slots__ will NOT prevent __dict__ "
                        "creation on the subclass. This behaviour is consistent "
                        "across versions but commonly misunderstood — and "
                        "Python 3.10 added clearer documentation and warnings "
                        "around this pattern."
                    ),
                    severity=Severity.INFO,
                    runtime=Runtime.CPYTHON,
                    affected_from="3.0",
                    suggestion=(
                        "Verify that all ancestor classes also define __slots__ "
                        "if you need to prevent __dict__ creation. "
                        "Use __slots__ = () on base classes that should not "
                        "have instance dictionaries."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/reference/"
                        "datamodel.html#slots"
                    ),
                ))
                break  # one finding per class

        return findings