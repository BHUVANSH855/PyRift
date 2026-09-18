"""
pyrift.analysis.calls
~~~~~~~~~~~~~~~~~~~~~
Shared call detection utilities.

Answers common questions:
  - Is function X called?
  - Is method X called on object Y?
  - What arguments were passed?

Alias/shadowing awareness (2026-09 audit #7-8): module-qualified calls
are resolved through :mod:`pyrift.analysis.symbols`, so
``import asyncio as aio; aio.get_event_loop()`` is recognised as a call
to ``asyncio.get_event_loop`` (previously a documented false negative --
see the CPY038 "aliased module not caught" golden case in
``benchmark/run_benchmark.py``), while a name that is shadowed elsewhere
in the file (e.g. ``asyncio = something_else``) is conservatively left
unresolved rather than guessing.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from .symbols import SymbolTable, build_symbol_table


@dataclass
class CallInfo:
    """Information about a single function/method call."""
    func_name: str        # e.g. "open" or "get_event_loop"
    module: str | None    # e.g. "asyncio" if asyncio.get_event_loop()
    line: int
    col: int
    node: ast.Call
    args: list[ast.expr]
    kwargs: dict[str, ast.expr]


def collect_calls(
    node: ast.AST,
    func_name: str,
    module: str | None = None,
    *,
    symbol_table: SymbolTable | None = None,
) -> list[CallInfo]:
    """
    Find all calls to func_name (optionally on module) in the AST.

    Examples:
        collect_calls(tree, "open")
        collect_calls(tree, "get_event_loop", module="asyncio")
        collect_calls(tree, "dumps", module="pickle")

    When *module* is given, the call target is resolved through import
    aliasing: ``import asyncio as aio; aio.get_event_loop()`` matches
    ``collect_calls(tree, "get_event_loop", module="asyncio")`` just
    like the unaliased form does. A name that is reassigned anywhere
    else in the file is treated conservatively as unresolved (see
    :mod:`pyrift.analysis.symbols`) rather than risking a false
    positive from shadowing.

    *symbol_table* lets a caller that already built one (e.g. because it
    calls ``collect_calls`` several times over the same tree) pass it in
    to avoid rebuilding it; otherwise one is built on demand.
    """
    results = []

    if module is not None and symbol_table is None:
        symbol_table = build_symbol_table(node)

    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue

        func = n.func
        kwargs = {
            kw.arg: kw.value
            for kw in n.keywords
            if kw.arg is not None
        }

        if module is None:
            # Bare function call: open(...), func(...)
            if isinstance(func, ast.Name) and func.id == func_name:
                results.append(CallInfo(
                    func_name=func_name,
                    module=None,
                    line=n.lineno,
                    col=n.col_offset,
                    node=n,
                    args=n.args,
                    kwargs=kwargs,
                ))
        else:
            # Module method call: asyncio.get_event_loop() -- including
            # through an import alias (aio.get_event_loop()).
            if (
                isinstance(func, ast.Attribute)
                and func.attr == func_name
                and isinstance(func.value, ast.Name)
            ):
                name = func.value.id
                matched = False

                if symbol_table is not None and name in symbol_table.shadowed:
                    # Reassigned elsewhere in the file -- refuse to
                    # attribute this call to any module, known or not.
                    matched = False
                elif (
                    symbol_table is not None
                    and name in symbol_table.module_aliases
                ):
                    # Name is a tracked import (possibly aliased) --
                    # trust the resolved canonical module over the
                    # literal spelling. This is what correctly rejects
                    # `import foo as asyncio; asyncio.get_event_loop()`
                    # (resolves to "foo", not "asyncio") as well as what
                    # correctly accepts
                    # `import asyncio as aio; aio.get_event_loop()`.
                    matched = symbol_table.module_aliases[name] == module
                elif name == module:
                    # Not a tracked import at all (e.g. no symbol table
                    # built, or the name wasn't captured by import
                    # collection) -- fall back to the legacy literal
                    # name match.
                    matched = True

                if matched:
                    results.append(CallInfo(
                        func_name=func_name,
                        module=module,
                        line=n.lineno,
                        col=n.col_offset,
                        node=n,
                        args=n.args,
                        kwargs=kwargs,
                    ))

    return results


def has_keyword_arg(call: ast.Call, arg_name: str) -> bool:
    """True if the call has a keyword argument with the given name."""
    return any(kw.arg == arg_name for kw in call.keywords)


def get_keyword_value(call: ast.Call,
                      arg_name: str) -> ast.expr | None:
    """Return the value of a keyword argument, or None."""
    for kw in call.keywords:
        if kw.arg == arg_name:
            return kw.value
    return None