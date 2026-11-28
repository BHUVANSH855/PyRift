"""
PPY057 -- copyreg.dispatch_table / pickle.dispatch_table behaves differently on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, ``pickle.Pickler`` uses ``copyreg.dispatch_table`` as a fallback
class-level dispatch table for custom pickling.  Mutations to
``copyreg.dispatch_table`` after a ``Pickler`` has been created are
immediately visible to that pickler (because CPython's C implementation
accesses the dict live).

On PyPy, the pure-Python ``pickle`` implementation may read the table at
construction time or behave differently when the table is mutated during
pickling.  Code that modifies ``copyreg.dispatch_table`` or
``pickle.Pickler.dispatch_table`` mid-stream and expects consistent
cross-runtime behaviour will have subtle bugs on PyPy.

Additionally, using the per-instance ``pickle.Pickler.dispatch_table``
attribute (available since Python 3.3) is the preferred pattern and avoids
the global-state issue entirely.

Documentation:
  https://doc.pypy.org/en/latest/cpython_differences.html
  https://docs.python.org/3/library/copyreg.html#copyreg.dispatch_table
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


def _is_dispatch_table_mutation(node: ast.stmt) -> tuple[bool, str]:
    """Return (True, description) if this statement mutates dispatch_table."""
    # copyreg.dispatch_table[...] = ...  or  copyreg.dispatch_table = ...
    # pickle.dispatch_table[...] = ...  or  pickle.dispatch_table = ...
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "dispatch_table"
                and isinstance(target.value, ast.Name)
                and target.value.id in ("copyreg", "pickle")
            ):
                return True, f"{target.value.id}.dispatch_table"
            if isinstance(target, ast.Subscript):
                val = target.value
                if (
                    isinstance(val, ast.Attribute)
                    and val.attr == "dispatch_table"
                    and isinstance(val.value, ast.Name)
                    and val.value.id in ("copyreg", "pickle")
                ):
                    return True, f"{val.value.id}.dispatch_table"
    # copyreg.dispatch_table.update(...)
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if isinstance(call.func, ast.Attribute) and call.func.attr in ("update", "clear", "pop"):
            obj = call.func.value
            if (
                isinstance(obj, ast.Attribute)
                and obj.attr == "dispatch_table"
                and isinstance(obj.value, ast.Name)
                and obj.value.id in ("copyreg", "pickle")
            ):
                return True, f"{obj.value.id}.dispatch_table"
    return False, ""


class CopyregDispatchTableRule(BaseRule):
    rule_id = "PPY057"
    title = "copyreg.dispatch_table / pickle.dispatch_table mutation differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for stmt in ast.walk(node):
            if not isinstance(stmt, ast.stmt):
                continue
            is_mutation, table_name = _is_dispatch_table_mutation(stmt)
            if not is_mutation:
                continue
            findings.append(Finding(
                    file=filename,
                    line=stmt.lineno,
                    col=stmt.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"Mutating {table_name} relies on CPython's C "
                        "implementation of Pickler reading the global "
                        "dispatch table live. PyPy's pure-Python pickle "
                        "may read the table at a different time, making "
                        "runtime-ordered mutations produce different results "
                        "than on CPython."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use the per-instance dispatch_table instead: "
                        "p = pickle.Pickler(f); "
                        "p.dispatch_table = copyreg.dispatch_table.copy(); "
                        "p.dispatch_table[MyClass] = my_reducer. "
                        "This avoids global state and works consistently "
                        "across runtimes."
                    ),
                    docs_url=(
                        "https://docs.python.org/3/library/copyreg.html"
                        "#copyreg.dispatch_table"
                    ),
                ))
        return findings