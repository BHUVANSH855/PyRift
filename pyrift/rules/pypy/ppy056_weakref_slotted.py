"""
PPY056 -- weakref to __slots__ class without __weakref__ slot fails differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, weakref.ref() to an instance of a __slots__ class without
"__weakref__" in the slots raises TypeError immediately. On PyPy, the
weakref may appear to be created successfully but then fail when dereferenced.

Documentation:
  https://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _slots_names(slots_node: ast.expr) -> list[str] | None:
    if isinstance(slots_node, (ast.Tuple, ast.List)):
        result = []
        for elt in slots_node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                result.append(elt.value)
            else:
                return None
        return result
    if isinstance(slots_node, ast.Constant) and isinstance(slots_node.value, str):
        return [slots_node.value]
    return None


class WeakrefSlottedRule(BaseRule):
    rule_id = "PPY056"
    title = "__slots__ class missing '__weakref__' slot: weakref failure timing differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

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
            slots_node: ast.expr | None = None
            for stmt in n.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and stmt.targets[0].id == "__slots__"
                ):
                    slots_node = stmt.value
                    break
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == "__slots__"
                    and stmt.value is not None
                ):
                    slots_node = stmt.value
                    break
            if slots_node is None:
                continue
            slots = _slots_names(slots_node)
            if slots is None:
                continue
            if "__weakref__" in slots:
                continue
            if not slots:
                continue
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    f"Class '{n.name}' uses __slots__ without including "
                    "'__weakref__'. On CPython, weakref.ref() to an instance "
                    "immediately raises TypeError. On PyPy, the weakref may "
                    "appear to be created successfully but then fail or return "
                    "None when dereferenced, making the error harder to find."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.PYPY,
                suggestion=(
                    f"If instances of '{n.name}' need to be weakly referenced, "
                    "add '__weakref__' to its __slots__ tuple. If weak references "
                    "are not needed, this is not a problem."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#differences-related-to-garbage-collection-strategies"
                ),
            ))
        return findings
