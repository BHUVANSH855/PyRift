"""
PPY009 — id() identity not stable between GC cycles on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, id() returns the memory address which is stable for
the lifetime of the object. On PyPy, objects may be moved by the
GC — id() can return different values for the same object across
GC cycles. Code using id() for caching or identity tracking may
silently produce wrong results on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class IdStabilityRule(BaseRule):
    rule_id = "PPY009"
    title   = "id() values not stable across GC cycles on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
        # Build parent map to detect id() used as dict key
        parent_map: dict[int, ast.AST] = {}
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parent_map[id(child)] = parent

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            if not (isinstance(func, ast.Name) and func.id == "id"):
                continue
            # Skip: id() used as a dict key — legitimate AST node identity pattern
            parent = parent_map.get(id(n))
            if isinstance(parent, ast.Index):
                continue
            # Skip: id(x) directly as subscript index parent_map[id(x)]
            grandparent = parent_map.get(id(parent)) if parent else None
            if isinstance(parent, ast.Subscript) or isinstance(grandparent, ast.Subscript):
                continue
            findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "id() returns the memory address on CPython — stable "
                        "for the object's lifetime. On PyPy, the GC may move "
                        "objects in memory, so id() can return different values "
                        "for the same object across GC cycles. Using id() for "
                        "caching, hashing, or identity tracking may silently "
                        "produce wrong results on PyPy."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use object identity with 'is' instead of comparing id() "
                        "values. For caching, use weakref or dedicated identity "
                        "maps rather than id()-based keys."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                    ),
                ))
        return findings