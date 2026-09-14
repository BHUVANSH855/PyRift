"""
CPY023 — multiprocessing fork start method changing in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The default multiprocessing start method on POSIX platforms (excluding
macOS, which has defaulted to 'spawn' since Python 3.8) changes from
'fork' to 'forkserver' in Python 3.14. Code relying on the default
'fork' behaviour may silently break.

Narrowed 2026-09-13 (review, point 7): a bare ``import multiprocessing``
is not evidence that a program relies on fork semantics -- plenty of
code imports the module and only ever uses ``Pool``/``Process`` in ways
that don't care about the start method. The rule now requires actual
use of a start-method-sensitive construct (``Process(...)``,
``Pool(...)``, or ``get_context()`` without an explicit method) before
firing, and is downgraded to MEDIUM confidence accordingly (see
``pyrift.rule_metadata``) since even that is still a proxy for "may be
fork-sensitive", not proof of it. Also excludes macOS, whose default was
never 'fork' to begin with, per the official multiprocessing docs.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

if TYPE_CHECKING:
    from pyrift.targets import TargetConfig

_EXCLUDED_PLATFORMS = {"windows", "win32", "macos", "darwin", "osx"}

# Constructs whose behavior can plausibly depend on the process start
# method. A bare `import multiprocessing` alone no longer triggers this
# rule -- see module docstring.
_START_METHOD_SENSITIVE_ATTRS = {"Process", "Pool", "get_context"}


def _collect_multiprocessing_bindings(
    node: ast.AST,
) -> tuple[set[str], set[str]]:
    """Return module aliases and directly imported sensitive symbols.

    The resolver is intentionally conservative. It understands only
    absolute imports of the `multiprocessing` package and the specific
    symbols this rule cares about. Unknown names are never treated as
    multiprocessing.
    """
    module_aliases: set[str] = set()
    symbol_aliases: set[str] = set()

    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                if alias.name == "multiprocessing":
                    module_aliases.add(alias.asname or "multiprocessing")
        elif (
            isinstance(n, ast.ImportFrom)
            and n.level == 0
            and n.module == "multiprocessing"
        ):
            for alias in n.names:
                if alias.name in _START_METHOD_SENSITIVE_ATTRS:
                    symbol_aliases.add(alias.asname or alias.name)

    return module_aliases, symbol_aliases


def _function_local_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    """Return names bound in the current function block.

    Nested functions and classes introduce separate code blocks, so their
    internal bindings must not be attributed to the containing function.
    Function/class definitions themselves still bind their names in the
    containing function block.

    Python determines function-local bindings for the entire function,
    so an assignment appearing after a call still shadows an outer
    binding at that call.
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
        """Collect bindings belonging to this function block only."""

        def visit_Global(self, node: ast.Global) -> None:
            global_names.update(node.names)

        def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
            nonlocal_names.update(node.names)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                local_names.add(node.id)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                local_names.add(node.name)

            # The exception handler body belongs to the current function
            # block, so continue traversing it. The handler's name itself
            # is already accounted for above.
            for statement in node.body:
                self.visit(statement)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # The function definition binds its own name in the current
            # block, but the nested function body is a separate block.
            local_names.add(node.name)

            # Defaults, decorators, and annotations are evaluated in the
            # containing scope, but they do not introduce local bindings.
            for decorator in node.decorator_list:
                self.visit(decorator)

            for default in (*node.args.defaults, *node.args.kw_defaults):
                if default is not None:
                    self.visit(default)

            for annotation in (
                [
                    arg.annotation
                    for arg in (
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                    )
                    if arg.annotation is not None
                ]
                + ([node.args.vararg.annotation]
                   if node.args.vararg
                   and node.args.vararg.annotation is not None
                   else [])
                + ([node.args.kwarg.annotation]
                   if node.args.kwarg
                   and node.args.kwarg.annotation is not None
                   else [])
            ):
                self.visit(annotation)

            if node.returns is not None:
                self.visit(node.returns)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            # Same scope rules as FunctionDef.
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            # The class name is bound in the containing function block, but
            # the class body has its own namespace and must not contribute
            # bindings to this function.
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


def _scope_for_call(
    node: ast.Call,
    function_scopes: list[tuple[ast.AST, set[str]]],
) -> set[str]:
    """Return the nearest containing function's local names."""
    return function_scopes[-1][1] if function_scopes else set()


def _has_explicit_start_method(node: ast.AST) -> bool:
    """Return True if the file already calls set_start_method or get_context
    with an explicit method argument."""
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        func = n.func
        if isinstance(func, ast.Attribute) and func.attr == "set_start_method":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "get_context" and n.args:
            # get_context("fork") / get_context("spawn") / etc. is already
            # explicit and version-safe.
            return True
    return False


def _uses_start_method_sensitive_api(
    node: ast.AST,
    module_aliases: set[str],
    symbol_aliases: set[str],
) -> ast.Call | None:
    """Return the first resolved call that depends on the default start
    method, or None if no known multiprocessing API is used.

    Function defaults, decorators, and annotations are evaluated outside
    the function body scope. Function bodies have their own local scope.
    Class bodies have their own namespace, while methods have independent
    function scopes and do not inherit class-local names.
    """

    function_scopes: list[set[str]] = []
    class_scopes: list[tuple[set[str], int]] = []

    def _class_local_names(class_node: ast.ClassDef) -> set[str]:
        """Return names bound directly in a class body.

        Nested function and class bodies introduce separate code blocks, so
        their internal bindings do not become bindings of this class body.
        Function/class definitions themselves bind their names in the class
        namespace.

        Expressions belonging to decorators, bases, keywords, defaults, and
        annotations are still traversed because calls in those expressions
        execute in the surrounding scope rather than in the nested body.
        """

        local_names: set[str] = set()

        class BindingCollector(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    local_names.add(node.id)

            def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
                if node.name:
                    local_names.add(node.name)

                for statement in node.body:
                    self.visit(statement)

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                local_names.add(node.name)

                for decorator in node.decorator_list:
                    self.visit(decorator)

                for default in (
                    *node.args.defaults,
                    *node.args.kw_defaults,
                ):
                    if default is not None:
                        self.visit(default)

                for arg in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                ):
                    if arg.annotation is not None:
                        self.visit(arg.annotation)

                if (
                    node.args.vararg is not None
                    and node.args.vararg.annotation is not None
                ):
                    self.visit(node.args.vararg.annotation)

                if (
                    node.args.kwarg is not None
                    and node.args.kwarg.annotation is not None
                ):
                    self.visit(node.args.kwarg.annotation)

                if node.returns is not None:
                    self.visit(node.returns)

            def visit_AsyncFunctionDef(
                self,
                node: ast.AsyncFunctionDef,
            ) -> None:
                local_names.add(node.name)

                for decorator in node.decorator_list:
                    self.visit(decorator)

                for default in (
                    *node.args.defaults,
                    *node.args.kw_defaults,
                ):
                    if default is not None:
                        self.visit(default)

                for arg in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                ):
                    if arg.annotation is not None:
                        self.visit(arg.annotation)

                if (
                    node.args.vararg is not None
                    and node.args.vararg.annotation is not None
                ):
                    self.visit(node.args.vararg.annotation)

                if (
                    node.args.kwarg is not None
                    and node.args.kwarg.annotation is not None
                ):
                    self.visit(node.args.kwarg.annotation)

                if node.returns is not None:
                    self.visit(node.returns)

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

    class Resolver(ast.NodeVisitor):
        result: ast.Call | None = None

        def _visit_function_definition(
            self,
            function: ast.FunctionDef | ast.AsyncFunctionDef,
        ) -> None:
            # Decorators, defaults, and annotations belong to the enclosing
            # scope of the function definition. They must therefore be
            # visited before entering the function's local scope.
            for decorator in function.decorator_list:
                self.visit(decorator)

            for default in (
                *function.args.defaults,
                *function.args.kw_defaults,
            ):
                if default is not None:
                    self.visit(default)

            for arg in (
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            ):
                if arg.annotation is not None:
                    self.visit(arg.annotation)

            if (
                function.args.vararg is not None
                and function.args.vararg.annotation is not None
            ):
                self.visit(function.args.vararg.annotation)

            if (
                function.args.kwarg is not None
                and function.args.kwarg.annotation is not None
            ):
                self.visit(function.args.kwarg.annotation)

            if function.returns is not None:
                self.visit(function.returns)

            if self.result is not None:
                return

            function_scopes.append(_function_local_names(function))
            try:
                for statement in function.body:
                    self.visit(statement)
            finally:
                function_scopes.pop()

        def visit_FunctionDef(
            self,
            function: ast.FunctionDef,
        ) -> None:
            self._visit_function_definition(function)

        def visit_AsyncFunctionDef(
            self,
            function: ast.AsyncFunctionDef,
        ) -> None:
            self._visit_function_definition(function)

        def visit_ClassDef(self, class_node: ast.ClassDef) -> None:
            # Decorators, bases, and keywords are evaluated in the
            # surrounding scope, not in the class namespace.
            for decorator in class_node.decorator_list:
                self.visit(decorator)

            for base in class_node.bases:
                self.visit(base)

            for keyword in class_node.keywords:
                self.visit(keyword.value)

            if self.result is not None:
                return

            class_scopes.append(
                (
                    _class_local_names(class_node),
                    len(function_scopes),
                )
            )
            try:
                for statement in class_node.body:
                    self.visit(statement)
            finally:
                class_scopes.pop()

        def visit_Call(self, call: ast.Call) -> None:
            if self.result is not None:
                return

            func = call.func

            if class_scopes:
                class_local_names, function_depth = class_scopes[-1]

                # A class body nested inside a function executes in the
                # class namespace, not in the enclosing function's local
                # namespace. Once a method/function is entered, however,
                # its own function scope takes precedence again.
                if len(function_scopes) == function_depth:
                    local_names = class_local_names
                elif function_scopes:
                    local_names = function_scopes[-1]
                else:
                    local_names = class_local_names
            elif function_scopes:
                local_names = function_scopes[-1]
            else:
                local_names = set()

            if isinstance(func, ast.Attribute):
                if (
                    func.attr in _START_METHOD_SENSITIVE_ATTRS
                    and isinstance(func.value, ast.Name)
                    and func.value.id in module_aliases
                    and func.value.id not in local_names
                ):
                    if func.attr == "get_context" and call.args:
                        return

                    self.result = call
                    return

            elif (
                isinstance(func, ast.Name)
                and func.id in symbol_aliases
                and func.id not in local_names
            ):
                if func.id == "get_context" and call.args:
                    return

                self.result = call
                return

            self.generic_visit(call)

    resolver = Resolver()
    resolver.visit(node)
    return resolver.result


class MultiprocessingForkRule(BaseRule):
    rule_id = "CPY023"
    title = "multiprocessing default start method changing in Python 3.14"
    runtime = "cpython"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        if (
            target_config is not None
            and target_config.platform is not None
            and target_config.platform.lower() in _EXCLUDED_PLATFORMS
        ):
            return []

        # If the file already sets the start method explicitly — no finding
        if _has_explicit_start_method(node):
            return []

        module_aliases, symbol_aliases = _collect_multiprocessing_bindings(node)

        if not module_aliases and not symbol_aliases:
            return []

        risky_call = _uses_start_method_sensitive_api(
            node,
            module_aliases,
            symbol_aliases,
        )
        if risky_call is None:
            # multiprocessing is imported but never used in a way that
            # plausibly depends on the start method -- nothing to report.
            return []

        return [Finding(
            file=filename,
            line=risky_call.lineno,
            col=risky_call.col_offset,
            rule_id=self.rule_id,
            title=self.title,
            description=(
                "The default multiprocessing start method on "
                "Linux/BSD/POSIX (excluding macOS) is 'fork' in Python "
                "<= 3.13. In Python 3.14 it changes to 'forkserver'. "
                "This file constructs a Process/Pool or calls "
                "get_context() without pinning a start method; if it "
                "relies on fork semantics (shared memory, inherited "
                "file descriptors, or process creation outside an "
                "`if __name__ == '__main__':` guard) it may silently "
                "break."
            ),
            severity=Severity.WARNING,
            runtime=Runtime.CPYTHON,
            affected_from="3.14",
            suggestion=(
                "Explicitly set the start method: "
                "multiprocessing.set_start_method('fork') "
                "or use multiprocessing.get_context('fork') "
                "to make the behaviour explicit and version-safe."
            ),
            docs_url=(
                "https://docs.python.org/3/library/multiprocessing.html"
                "#contexts-and-start-methods"
            ),
        )]