"""
pyrift.analysis.guards
~~~~~~~~~~~~~~~~~~~~~~
Version guards, implementation guards, ``TYPE_CHECKING`` blocks, and
try/except compatibility shims -- built once per file and used as a
generic post-processing filter over findings from *any* rule.

Why this exists
----------------
The 2026-09 architecture review (points 73-78) identified that PyRift's
biggest source of false positives on real-world libraries is code that
already handles the compatibility concern correctly:

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self

    if sys.implementation.name == "pypy":
        ...  # deliberately PyPy-specific code

A naive per-rule AST match flags the exact code written to *avoid* the
problem. Rather than threading a semantic context object through all
118 rule ``check()`` implementations (a much larger, riskier refactor),
this module builds a single ``GuardIndex`` per file and the scanner
applies it as a generic filter: any finding whose line falls inside a
guard that logically neutralises it is suppressed or downgraded,
independent of which rule produced it.

This is intentionally conservative: it only recognises a small set of
well-established, syntactically explicit patterns. It does not attempt
general control-flow or data-flow analysis.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class VersionGuard:
    """A ``sys.version_info`` comparison guarding a block of code."""

    min_version: tuple[int, ...] | None  # block runs only when >= this
    max_version: tuple[int, ...] | None  # block runs only when < this


@dataclass
class GuardIndex:
    """Per-file index of guarded/shimmed line ranges.

    All ranges are inclusive (start_line, end_line) in 1-based line
    numbers, matching ``ast`` node ``lineno``/``end_lineno``.
    """

    # (start, end, guard) for `if sys.version_info ...:` bodies
    version_guards: list[tuple[int, int, VersionGuard]] = field(default_factory=list)
    # (start, end) ranges that only execute when the implementation IS PyPy
    pypy_only_ranges: list[tuple[int, int]] = field(default_factory=list)
    # (start, end) ranges that only execute when the implementation is NOT PyPy
    cpython_only_ranges: list[tuple[int, int]] = field(default_factory=list)
    # (start, end) ranges inside `if TYPE_CHECKING:` blocks (never run at runtime)
    type_checking_ranges: list[tuple[int, int]] = field(default_factory=list)
    # (start, end) ranges that are part of a try/except ImportError
    # (or bare except) compatibility shim -- covers both the try body
    # and the except body(ies).
    import_shim_ranges: list[tuple[int, int]] = field(default_factory=list)

    # -- queries -----------------------------------------------------

    def version_guard_at(self, line: int) -> VersionGuard | None:
        best: VersionGuard | None = None
        best_span = None
        for start, end, guard in self.version_guards:
            if start <= line <= end:
                span = end - start
                if best_span is None or span < best_span:
                    best, best_span = guard, span
        return best

    def is_pypy_only(self, line: int) -> bool:
        return any(start <= line <= end for start, end in self.pypy_only_ranges)

    def is_cpython_only(self, line: int) -> bool:
        return any(start <= line <= end for start, end in self.cpython_only_ranges)

    def is_type_checking_only(self, line: int) -> bool:
        return any(start <= line <= end for start, end in self.type_checking_ranges)

    def is_import_shim(self, line: int) -> bool:
        return any(start <= line <= end for start, end in self.import_shim_ranges)


def _const_tuple(node: ast.AST) -> tuple[int, ...] | None:
    if not isinstance(node, ast.Tuple):
        return None
    values = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, int):
            values.append(elt.value)
        else:
            return None
    return tuple(values)


def _is_version_info(node: ast.AST) -> bool:
    """Match ``sys.version_info`` or ``sys.version_info[:2]``."""
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "version_info"
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    ):
        return True
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "version_info"
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "sys"
    )


def _is_pypy_check(node: ast.AST) -> bool | None:
    """Return True for an explicit "this is PyPy" check, False for
    an explicit "this is NOT PyPy" check, None if not such a check.

    Recognises::

        sys.implementation.name == "pypy"
        sys.implementation.name != "pypy"
        platform.python_implementation() == "PyPy"
        platform.python_implementation() != "PyPy"
    """
    if not (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
    ):
        return None

    left = node.left
    op = node.ops[0]
    right = node.comparators[0]

    def _is_impl_name(n: ast.AST) -> bool:
        return (
            isinstance(n, ast.Attribute)
            and n.attr == "name"
            and isinstance(n.value, ast.Attribute)
            and n.value.attr == "implementation"
            and isinstance(n.value.value, ast.Name)
            and n.value.value.id == "sys"
        )

    def _is_python_implementation_call(n: ast.AST) -> bool:
        return (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "python_implementation"
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "platform"
        )

    def _pypy_literal(n: ast.AST) -> bool:
        return isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.lower() == "pypy"

    if _is_impl_name(left) and _pypy_literal(right) or _is_python_implementation_call(left) and _pypy_literal(right):
        matches_pypy = True
    else:
        return None

    if isinstance(op, ast.Eq):
        return True if matches_pypy else None
    if isinstance(op, ast.NotEq):
        return False if matches_pypy else None
    return None


def _build_parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    parent_map: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[id(child)] = parent
    return parent_map


def _span(nodes: list[ast.stmt]) -> tuple[int, int] | None:
    if not nodes:
        return None
    start = min(n.lineno for n in nodes)
    end = max(getattr(n, "end_lineno", n.lineno) or n.lineno for n in nodes)
    return start, end


def build_guard_index(tree: ast.AST) -> GuardIndex:
    """Build a :class:`GuardIndex` for an entire module AST."""
    index = GuardIndex()

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test

            # --- version guards -----------------------------------
            if (
                isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and len(test.comparators) == 1
                and _is_version_info(test.left)
            ):
                op = test.ops[0]
                version = _const_tuple(test.comparators[0])
                if version is not None:
                    body_span = _span(node.body)
                    else_span = _span(node.orelse) if node.orelse else None

                    if isinstance(op, (ast.GtE, ast.Gt)):
                        min_v = version if isinstance(op, ast.GtE) else (
                            version[:-1] + (version[-1] + 1,) if version else version
                        )
                        if body_span:
                            index.version_guards.append(
                                (*body_span, VersionGuard(min_version=min_v, max_version=None))
                            )
                        if else_span:
                            index.version_guards.append(
                                (*else_span, VersionGuard(min_version=None, max_version=min_v))
                            )
                    elif isinstance(op, (ast.LtE, ast.Lt)):
                        max_v = version if isinstance(op, ast.Lt) else (
                            version[:-1] + (version[-1] + 1,) if version else version
                        )
                        if body_span:
                            index.version_guards.append(
                                (*body_span, VersionGuard(min_version=None, max_version=max_v))
                            )
                        if else_span:
                            index.version_guards.append(
                                (*else_span, VersionGuard(min_version=max_v, max_version=None))
                            )

            # --- implementation guards -----------------------------
            pypy_check = _is_pypy_check(test)
            if pypy_check is not None:
                body_span = _span(node.body)
                else_span = _span(node.orelse) if node.orelse else None
                if pypy_check:
                    if body_span:
                        index.pypy_only_ranges.append(body_span)
                    if else_span:
                        index.cpython_only_ranges.append(else_span)
                else:
                    if body_span:
                        index.cpython_only_ranges.append(body_span)
                    if else_span:
                        index.pypy_only_ranges.append(else_span)

            # --- TYPE_CHECKING --------------------------------------
            if (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (
                    isinstance(test, ast.Attribute)
                    and test.attr == "TYPE_CHECKING"
                )
            ):
                body_span = _span(node.body)
                if body_span:
                    index.type_checking_ranges.append(body_span)

        # --- try/except ImportError compatibility shims -------------
        if isinstance(node, ast.Try):
            has_import_error_handler = False
            for handler in node.handlers:
                handler_type = handler.type
                if handler_type is None:
                    has_import_error_handler = True  # bare except
                elif isinstance(handler_type, ast.Name) and handler_type.id in (
                    "ImportError",
                    "ModuleNotFoundError",
                ) or isinstance(handler_type, ast.Tuple) and any(
                    isinstance(e, ast.Name)
                    and e.id in ("ImportError", "ModuleNotFoundError")
                    for e in handler_type.elts
                ):
                    has_import_error_handler = True

            if has_import_error_handler:
                try_span = _span(node.body)
                if try_span:
                    index.import_shim_ranges.append(try_span)
                for handler in node.handlers:
                    handler_span = _span(handler.body)
                    if handler_span:
                        index.import_shim_ranges.append(handler_span)

    return index


def guard_reduces_risk(
    index: GuardIndex,
    line: int,
    *,
    finding_runtime: str,
    affected_from: str,
    affected_until: str,
    category: str,
) -> tuple[bool, str]:
    """Decide whether a finding at *line* is neutralised by a detected
    guard/shim.

    Returns ``(should_suppress, reason)``. ``reason`` is always set when
    ``should_suppress`` is True, and is also set (non-empty) when the
    finding should be *downgraded* rather than dropped (currently only
    the ``TYPE_CHECKING`` case, signalled by returning
    ``should_suppress=False`` with a reason) -- callers should check the
    reason string to decide which of the two applies.
    """
    # TYPE_CHECKING: code never executes at runtime. Downgrade, don't drop
    # -- this can still matter for users running a type checker on an
    # older interpreter, which is a legitimate (if narrower) concern.
    if index.is_type_checking_only(line):
        return False, "inside `if TYPE_CHECKING:` -- never executes at runtime"

    # Implementation guards.
    if finding_runtime == "cpython" and index.is_pypy_only(line):
        return True, "inside a PyPy-only branch (sys.implementation.name == 'pypy'); never runs on CPython"
    if finding_runtime == "pypy" and index.is_cpython_only(line):
        return True, "inside a CPython-only branch; never runs on PyPy"

    # Compatibility shims: only suppress pure API-availability
    # (compatibility) findings -- a shim doesn't neutralise a genuine
    # silent semantic difference, only an ImportError/AttributeError risk.
    if category == "compatibility" and index.is_import_shim(line):
        return True, "inside a try/except ImportError compatibility shim"

    # Version guards for compatibility (introduced/removed-API) findings.
    if category == "compatibility" and (affected_from or affected_until):
        guard = index.version_guard_at(line)
        if guard is not None:
            if affected_from and guard.min_version is not None:
                # "requires >= affected_from" and code only runs when the
                # interpreter is already new enough.
                try:
                    from_tuple = tuple(int(p) for p in affected_from.split("."))
                except ValueError:
                    from_tuple = None
                if from_tuple is not None and guard.min_version >= from_tuple:
                    return True, (
                        f"inside `if sys.version_info >= {guard.min_version}:` "
                        f"which already satisfies the {affected_from}+ requirement"
                    )
            if affected_until and guard.max_version is not None:
                try:
                    until_tuple = tuple(int(p) for p in affected_until.split("."))
                except ValueError:
                    until_tuple = None
                if until_tuple is not None and guard.max_version <= until_tuple:
                    return True, (
                        f"inside `if sys.version_info < {guard.max_version}:` "
                        "which only runs before the affected version"
                    )

    return False, ""
