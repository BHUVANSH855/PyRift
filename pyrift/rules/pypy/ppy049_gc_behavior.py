"""
PPY049 — GC behavior differences on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
PyPy uses a different garbage collection strategy than CPython:
  - PyPy uses a generational GC with different thresholds
  - gc.collect() may trigger different objects to be collected
  - gc.get_objects() returns different object counts
  - Weakref callbacks may fire at different times
  - gc.disable() has different effects on reference counting

Code that depends on deterministic GC timing or gc.collect() behavior
may behave differently on PyPy.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class GcBehaviorRule(BaseRule):
    rule_id = "PPY049"
    title = "GC behavior differs between PyPy and CPython"
    runtime = "pypy"
    severity = Severity.WARNING

    _GC_FUNCTIONS = frozenset(
        {
            "collect",
            "get_objects",
            "get_count",
            "set_threshold",
            "get_referrers",
            "get_referents",
            "disable",
            "enable",
        }
    )

    @staticmethod
    def _scope_bindings(
        body: list[ast.stmt],
    ) -> tuple[set[str], set[str]]:
        """
        Return (gc_imports, local_bindings) for one lexical scope.

        Nested functions, classes, and lambdas are separate scopes and are
        intentionally excluded from this analysis.
        """
        gc_imports: set[str] = set()
        local_bindings: set[str] = set()

        def visit(node: ast.AST) -> None:
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                return

            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".", 1)[0]
                    local_bindings.add(name)

                    if alias.name == "gc":
                        gc_imports.add(name)

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local_bindings.add(alias.asname or alias.name)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    for child in ast.walk(target):
                        if isinstance(child, ast.Name):
                            local_bindings.add(child.id)

            elif isinstance(
                node,
                (ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor),
            ):
                for child in ast.walk(node.target):
                    if isinstance(child, ast.Name):
                        local_bindings.add(child.id)

            elif isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if item.optional_vars is not None:
                        for child in ast.walk(item.optional_vars):
                            if isinstance(child, ast.Name):
                                local_bindings.add(child.id)

            elif isinstance(node, ast.NamedExpr):
                local_bindings.add(node.target.id)

            elif isinstance(node, ast.ExceptHandler) and node.name:
                local_bindings.add(node.name)

            for child in ast.iter_child_nodes(node):
                visit(child)

        for statement in body:
            visit(statement)

        return gc_imports, local_bindings

    @classmethod
    def _gc_name_for_scope(
        cls,
        body: list[ast.stmt],
        inherited_gc_name: str | None = None,
    ) -> str | None:
        """
        Return the gc-module binding for one lexical scope.

        A local binding always shadows an inherited binding.  Only an
        explicit ``import gc`` or ``import gc as alias`` establishes a
        module binding in the current scope.
        """
        gc_imports, local_bindings = cls._scope_bindings(body)

        if inherited_gc_name is not None:
            if inherited_gc_name in local_bindings:
                if inherited_gc_name in gc_imports:
                    return inherited_gc_name
                return None

            return inherited_gc_name

        for name in gc_imports:
            if name in local_bindings:
                return name

        return None

    @staticmethod
    def _scope_body(
        body: list[ast.stmt],
    ) -> list[ast.AST]:
        """
        Return nodes belonging to this lexical scope.

        Nested functions, classes, and lambdas are separate scopes and are
        deliberately not traversed.
        """
        result: list[ast.AST] = []

        def visit(node: ast.AST) -> None:
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Lambda,
                ),
            ):
                return

            result.append(node)

            for child in ast.iter_child_nodes(node):
                visit(child)

        for statement in body:
            visit(statement)

        return result

    def _findings_in_scope(
        self,
        body: list[ast.stmt],
        gc_name: str | None,
        filename: str,
    ) -> list[Finding]:
        if gc_name is None:
            return []

        findings: list[Finding] = []

        for current in self._scope_body(body):
            if not isinstance(current, ast.Call):
                continue

            func = current.func

            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == gc_name
                and func.attr in self._GC_FUNCTIONS
            ):
                continue

            if func.attr in {"disable", "enable"}:
                description = (
                    f"gc.{func.attr}() has different effects on PyPy. "
                    "PyPy's GC is less dependent on reference counting, "
                    "so disabling GC may not prevent collection as "
                    "expected."
                )
                suggestion = (
                    "Avoid relying on gc.disable()/enable() for "
                    "controlling object lifetime. Use weak references "
                    "or explicit cleanup patterns instead."
                )
            else:
                description = (
                    f"gc.{func.attr}() behaves differently on PyPy. "
                    "PyPy uses a generational GC with different "
                    "thresholds and collection strategies. "
                    "gc.collect() may trigger different objects to "
                    "be collected, and gc.get_objects() returns "
                    "different counts."
                )
                suggestion = (
                    "Do not rely on deterministic GC timing or exact "
                    "gc.get_objects() counts. For memory management, "
                    "use context managers and explicit cleanup instead."
                )

            findings.append(
                Finding(
                    file=filename,
                    line=current.lineno,
                    col=current.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=description,
                    severity=self.severity,
                    runtime=Runtime.PYPY,
                    suggestion=suggestion,
                    docs_url=(
                        "https://doc.pypy.org/en/latest/"
                        "cpython_differences.html"
                    ),
                )
            )

        return findings

    def _scan_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_gc_name: str | None,
        filename: str,
    ) -> list[Finding]:
        local_gc_name = self._gc_name_for_scope(
            node.body,
            inherited_gc_name=module_gc_name,
        )

        findings = self._findings_in_scope(
            node.body,
            local_gc_name,
            filename,
        )

        for statement in node.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                findings.extend(
                    self._scan_function(
                        statement,
                        local_gc_name,
                        filename,
                    )
                )

        return findings

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if not isinstance(node, ast.Module):
            return []

        module_gc_name = self._gc_name_for_scope(node.body)

        findings = self._findings_in_scope(
            node.body,
            module_gc_name,
            filename,
        )

        for statement in node.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                findings.extend(
                    self._scan_function(
                        statement,
                        module_gc_name,
                        filename,
                    )
                )

        return findings
