"""
pyrift.analysis.calls
~~~~~~~~~~~~~~~~~~~~~
Shared call detection utilities.

Answers common questions:
  - Is function X called?
  - Is method X called on object Y?
  - What arguments were passed?
"""
from __future__ import annotations

import ast
from dataclasses import dataclass


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


def collect_calls(node: ast.AST, func_name: str,
                  module: str | None = None) -> list[CallInfo]:
    """
    Find all calls to func_name (optionally on module) in the AST.

    Examples:
        collect_calls(tree, "open")
        collect_calls(tree, "get_event_loop", module="asyncio")
        collect_calls(tree, "dumps", module="pickle")
    """
    results = []

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
            # Module method call: asyncio.get_event_loop()
            if (isinstance(func, ast.Attribute) and
                    func.attr == func_name and
                    isinstance(func.value, ast.Name) and
                    func.value.id == module):
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