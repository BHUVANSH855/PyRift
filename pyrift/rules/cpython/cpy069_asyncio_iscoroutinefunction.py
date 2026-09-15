"""
CPY069 — asyncio.iscoroutinefunction() deprecated in 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
asyncio.iscoroutinefunction() was deprecated in Python 3.14 in favor of
inspect.iscoroutinefunction(). It is scheduled for removal in Python 3.16.

Detects:
  asyncio.iscoroutinefunction(func)
  import asyncio as aio; aio.iscoroutinefunction(func)
  from asyncio import iscoroutinefunction
  from asyncio import iscoroutinefunction as is_cf
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

if TYPE_CHECKING:
    from pyrift.targets import TargetConfig


def _function_local_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    """Return names bound in the current function block.

    Nested functions and classes introduce separate code blocks, so their
    internal bindings do not become bindings of the containing function.
    """
    local_names: set[str] = set()

    for arg in (
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    ):
        local_names.add(arg.arg)

    if function.args.vararg is not None:
        local_names.add(function.args.vararg.arg)

    if function.args.kwarg is not None:
        local_names.add(function.args.kwarg.arg)

    global_names: set[str] = set()
    nonlocal_names: set[str] = set()

    class BindingCollector(ast.NodeVisitor):
        def visit_Global(self, node: ast.Global) -> None:
            global_names.update(node.names)

        def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
            nonlocal_names.update(node.names)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                local_names.add(node.id)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                local_names.add(alias.asname or alias.name.split(".", 1)[0])

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for alias in node.names:
                if alias.name != "*":
                    local_names.add(alias.asname or alias.name)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                local_names.add(node.name)
            for statement in node.body:
                self.visit(statement)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            local_names.add(node.name)

            for decorator in node.decorator_list:
                self.visit(decorator)

            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

            for arg in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ):
                if arg.annotation is not None:
                    self.visit(arg.annotation)

            if node.args.vararg is not None and node.args.vararg.annotation is not None:
                self.visit(node.args.vararg.annotation)

            if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
                self.visit(node.args.kwarg.annotation)

            if node.returns is not None:
                self.visit(node.returns)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            local_names.add(node.name)

            for decorator in node.decorator_list:
                self.visit(decorator)

            for base in node.bases:
                self.visit(base)

            for keyword in node.keywords:
                self.visit(keyword.value)

    collector = BindingCollector()

    for statement in function.body:
        collector.visit(statement)

    local_names.difference_update(global_names)
    local_names.difference_update(nonlocal_names)

    return local_names


def _collect_module_bindings(
    node: ast.Module,
) -> tuple[set[str], set[str], set[str]]:
    """Collect module-level asyncio and shadowing bindings."""
    asyncio_modules: set[str] = set()
    asyncio_symbols: set[str] = set()
    other_bindings: set[str] = set()

    for statement in node.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bound_name = alias.asname or alias.name.split(".", 1)[0]

                if alias.name == "asyncio":
                    asyncio_modules.add(bound_name)
                else:
                    other_bindings.add(bound_name)

        elif isinstance(statement, ast.ImportFrom):
            if statement.level == 0 and statement.module == "asyncio":
                for alias in statement.names:
                    if alias.name == "iscoroutinefunction":
                        asyncio_symbols.add(alias.asname or alias.name)
                    elif alias.name != "*":
                        other_bindings.add(alias.asname or alias.name)
            else:
                for alias in statement.names:
                    if alias.name != "*":
                        other_bindings.add(alias.asname or alias.name)

        elif isinstance(
            statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            other_bindings.add(statement.name)

        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    other_bindings.add(target.id)

        elif isinstance(
            statement,
            (
                ast.AnnAssign,
                ast.AugAssign,
                ast.NamedExpr,
                ast.For,
                ast.AsyncFor,
            ),
        ):
            if isinstance(statement.target, ast.Name):
                other_bindings.add(statement.target.id)

        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                if isinstance(item.optional_vars, ast.Name):
                    other_bindings.add(item.optional_vars.id)

        elif isinstance(statement, ast.Try):
            for handler in statement.handlers:
                if handler.name:
                    other_bindings.add(handler.name)

    asyncio_modules.difference_update(other_bindings)
    asyncio_symbols.difference_update(other_bindings)

    return asyncio_modules, asyncio_symbols, other_bindings


def _function_asyncio_bindings(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[set[str], set[str]]:
    """Return effective asyncio bindings introduced in one function scope."""
    asyncio_modules: set[str] = set()
    asyncio_symbols: set[str] = set()
    other_bindings: set[str] = set()

    class ImportCollector(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                bound_name = alias.asname or alias.name.split(".", 1)[0]

                if alias.name == "asyncio":
                    asyncio_modules.add(bound_name)
                else:
                    other_bindings.add(bound_name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level == 0 and node.module == "asyncio":
                for alias in node.names:
                    if alias.name == "iscoroutinefunction":
                        asyncio_symbols.add(alias.asname or alias.name)
                    elif alias.name != "*":
                        other_bindings.add(alias.asname or alias.name)
            else:
                for alias in node.names:
                    if alias.name != "*":
                        other_bindings.add(alias.asname or alias.name)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                other_bindings.add(node.id)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                other_bindings.add(node.name)

            for statement in node.body:
                self.visit(statement)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            other_bindings.add(node.name)

            for decorator in node.decorator_list:
                self.visit(decorator)

            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

            for arg in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ):
                if arg.annotation is not None:
                    self.visit(arg.annotation)

            if node.args.vararg is not None and node.args.vararg.annotation is not None:
                self.visit(node.args.vararg.annotation)

            if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
                self.visit(node.args.kwarg.annotation)

            if node.returns is not None:
                self.visit(node.returns)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            other_bindings.add(node.name)

            for decorator in node.decorator_list:
                self.visit(decorator)

            for base in node.bases:
                self.visit(base)

            for keyword in node.keywords:
                self.visit(keyword.value)

    collector = ImportCollector()

    for statement in function.body:
        collector.visit(statement)

    asyncio_modules.difference_update(other_bindings)
    asyncio_symbols.difference_update(other_bindings)

    return asyncio_modules, asyncio_symbols


def _class_local_names(class_node: ast.ClassDef) -> set[str]:
    """Return names bound directly in a class namespace."""
    local_names: set[str] = set()

    class BindingCollector(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                local_names.add(node.id)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                local_names.add(alias.asname or alias.name.split(".", 1)[0])

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level == 0:
                for alias in node.names:
                    if alias.name != "*":
                        local_names.add(alias.asname or alias.name)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                local_names.add(node.name)
            for statement in node.body:
                self.visit(statement)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            local_names.add(node.name)

            for decorator in node.decorator_list:
                self.visit(decorator)

            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

            for arg in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ):
                if arg.annotation is not None:
                    self.visit(arg.annotation)

            if node.args.vararg is not None and node.args.vararg.annotation is not None:
                self.visit(node.args.vararg.annotation)

            if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
                self.visit(node.args.kwarg.annotation)

            if node.returns is not None:
                self.visit(node.returns)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            local_names.add(node.name)

            for decorator in node.decorator_list:
                self.visit(decorator)

            for base in node.bases:
                self.visit(base)

            for keyword in node.keywords:
                self.visit(keyword.value)

    collector = BindingCollector()

    for statement in class_node.body:
        collector.visit(statement)

    return local_names


class _Resolver(ast.NodeVisitor):
    """Resolve CPY069 calls while respecting Python scope boundaries."""

    def __init__(
        self,
        rule: AsyncioIscoroutinefunctionRule,
        filename: str,
        module_modules: set[str],
        module_symbols: set[str],
        module_other_bindings: set[str],
    ) -> None:
        self.rule = rule
        self.filename = filename
        self.module_modules = module_modules
        self.module_symbols = module_symbols
        self.module_other_bindings = module_other_bindings
        self.function_scopes: list[tuple[set[str], set[str], set[str]]] = []
        self.class_scopes: list[set[str]] = []
        self.findings: list[Finding] = []

    def _current_bindings(self) -> tuple[set[str], set[str]]:
        if self.function_scopes:
            local_names, local_modules, local_symbols = self.function_scopes[-1]

            modules = set(local_modules)
            symbols = set(local_symbols)

            for name in self.module_modules:
                if name not in local_names:
                    modules.add(name)

            for name in self.module_symbols:
                if name not in local_names:
                    symbols.add(name)

            return modules, symbols

        if self.class_scopes:
            class_names = self.class_scopes[-1]

            modules = {name for name in self.module_modules if name not in class_names}
            symbols = {name for name in self.module_symbols if name not in class_names}

            return modules, symbols

        return self.module_modules, self.module_symbols

    def _visit_function(
        self,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        local_names = _function_local_names(function)
        local_modules, local_symbols = _function_asyncio_bindings(function)

        self.function_scopes.append((local_names, local_modules, local_symbols))

        try:
            for statement in function.body:
                self.visit(statement)
        finally:
            self.function_scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)

        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)

        for arg in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ):
            if arg.annotation is not None:
                self.visit(arg.annotation)

        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            self.visit(node.args.vararg.annotation)

        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            self.visit(node.args.kwarg.annotation)

        if node.returns is not None:
            self.visit(node.returns)

        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)

        for base in node.bases:
            self.visit(base)

        for keyword in node.keywords:
            self.visit(keyword.value)

        class_names = _class_local_names(node)
        self.class_scopes.append(class_names)

        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self.class_scopes.pop()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level == 0 and node.module == "asyncio":
            _, asyncio_symbols = self._current_bindings()

            for alias in node.names:
                if alias.name != "iscoroutinefunction":
                    continue

                bound_name = alias.asname or alias.name

                if bound_name in asyncio_symbols:
                    self.findings.append(
                        self.rule._make(
                            self.filename,
                            node.lineno,
                            node.col_offset,
                        )
                    )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        module_aliases, _ = self._current_bindings()

        if (
            isinstance(func, ast.Attribute)
            and func.attr == "iscoroutinefunction"
            and isinstance(func.value, ast.Name)
            and func.value.id in module_aliases
        ):
            self.findings.append(
                self.rule._make(
                    self.filename,
                    node.lineno,
                    node.col_offset,
                )
            )

        self.generic_visit(node)


class AsyncioIscoroutinefunctionRule(BaseRule):
    rule_id = "CPY069"
    title = "asyncio.iscoroutinefunction() deprecated in Python 3.14"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if not isinstance(node, ast.Module):
            return []

        (
            module_modules,
            module_symbols,
            module_other_bindings,
        ) = _collect_module_bindings(node)

        resolver = _Resolver(
            self,
            filename,
            module_modules,
            module_symbols,
            module_other_bindings,
        )
        resolver.visit(node)

        seen: set[tuple[int, int]] = set()
        unique: list[Finding] = []

        for finding in resolver.findings:
            key = (finding.line, finding.col)

            if key not in seen:
                seen.add(key)
                unique.append(finding)

        return unique

    def _make(self, filename: str, line: int, col: int) -> Finding:
        return Finding(
            file=filename,
            line=line,
            col=col,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "asyncio.iscoroutinefunction() is deprecated since Python 3.14. "
                "Use inspect.iscoroutinefunction() instead."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Replace asyncio.iscoroutinefunction(func) with "
                "inspect.iscoroutinefunction(func)."
            ),
            docs_url="https://docs.python.org/3/whatsnew/3.14.html",
        )
