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


# Sentinels for "unbounded" ends of a version interval. Real version
# tuples always start with a non-negative major version, and no
# realistic Python major version will ever reach 9999, so these sort
# strictly below/above any real version tuple under tuple comparison.
_NEG_INF: tuple[int, ...] = (-1,)
_POS_INF: tuple[int, ...] = (9999,)


def _parse_version(text: str) -> tuple[int, ...] | None:
    """Parse a dotted version string like ``"3.15"`` into ``(3, 15)``.

    Returns ``None`` (rather than raising) for malformed input so callers
    can fall back to "no bound known" instead of crashing on bad metadata.
    """
    try:
        return tuple(int(p) for p in text.split("."))
    except ValueError:
        return None


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
        return (
            isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and n.value.lower() == "pypy"
        )

    if (
        _is_impl_name(left)
        and _pypy_literal(right)
        or _is_python_implementation_call(left)
        and _pypy_literal(right)
    ):
        matches_pypy = True
    else:
        return None

    if isinstance(op, ast.Eq):
        return True if matches_pypy else None
    if isinstance(op, ast.NotEq):
        return False if matches_pypy else None
    return None


def _version_guard_from_test(test: ast.expr) -> VersionGuard | None:
    """If *test* is a single ``sys.version_info <op> (X, Y)`` comparison,
    return the ``VersionGuard`` describing when it is True. Returns
    ``None`` for anything else (implementation checks, boolean
    combinations, non-version tests, etc.)."""
    if not (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and len(test.comparators) == 1
        and _is_version_info(test.left)
    ):
        return None

    op = test.ops[0]
    version = _const_tuple(test.comparators[0])
    if version is None:
        return None

    if isinstance(op, (ast.GtE, ast.Gt)):
        min_v = (
            version
            if isinstance(op, ast.GtE)
            else (version[:-1] + (version[-1] + 1,) if version else version)
        )
        return VersionGuard(min_version=min_v, max_version=None)

    if isinstance(op, (ast.LtE, ast.Lt)):
        max_v = (
            version
            if isinstance(op, ast.Lt)
            else (version[:-1] + (version[-1] + 1,) if version else version)
        )
        return VersionGuard(min_version=None, max_version=max_v)

    return None


def _negate_guard(guard: VersionGuard) -> VersionGuard:
    """The complement of a single-bound guard from an `if` test: the
    version range for which the test is False. Only meaningful for the
    single-clause guards ``_version_guard_from_test`` produces (each has
    exactly one bound set)."""
    if guard.min_version is not None and guard.max_version is None:
        return VersionGuard(min_version=None, max_version=guard.min_version)
    if guard.max_version is not None and guard.min_version is None:
        return VersionGuard(min_version=guard.max_version, max_version=None)
    # Already both-bounded or fully unbounded -- nothing principled to
    # negate into a single interval; treat as "no additional info".
    return VersionGuard(min_version=None, max_version=None)


def _intersect_guards(a: VersionGuard, b: VersionGuard) -> VersionGuard:
    """Compose two guards into the version range where *both* hold --
    this is what makes nested/elif version checks interval-correct
    instead of only ever considering the innermost `if` in isolation
    (2026-09 audit #4)."""
    if a.min_version is None:
        min_v = b.min_version
    elif b.min_version is None:
        min_v = a.min_version
    else:
        min_v = max(a.min_version, b.min_version)

    if a.max_version is None:
        max_v = b.max_version
    elif b.max_version is None:
        max_v = a.max_version
    else:
        max_v = min(a.max_version, b.max_version)

    return VersionGuard(min_version=min_v, max_version=max_v)


# Statement containers pyrift recurses into to propagate an ambient
# version-guard context down to nested code (so a guard higher up the
# tree still applies inside a nested function/try/for/with/class body).
_CONTAINER_BODY_ATTRS = ("body", "orelse", "finalbody")


def _child_statement_lists(node: ast.AST) -> list[list[ast.stmt]]:
    lists: list[list[ast.stmt]] = []
    for attr in _CONTAINER_BODY_ATTRS:
        value = getattr(node, attr, None)
        if value:
            lists.append(value)
    if isinstance(node, ast.Try):
        for handler in node.handlers:
            if handler.body:
                lists.append(handler.body)
    return lists


def _walk_version_context(
    statements: list[ast.stmt],
    context: VersionGuard,
    index: GuardIndex,
) -> None:
    """Recursively compose ``sys.version_info`` guards through nested
    ``if``/``elif``/``else`` chains (and down through function/class/
    try/for/while/with bodies), so a line deep inside several nested or
    chained guards gets the *intersection* of all of them, not just its
    immediately-enclosing ``if``.
    """
    for stmt in statements:
        if isinstance(stmt, ast.If):
            guard_here = _version_guard_from_test(stmt.test)

            if guard_here is not None:
                body_context = _intersect_guards(context, guard_here)
                body_span = _span(stmt.body)
                if body_span:
                    index.version_guards.append((*body_span, body_context))
                _walk_version_context(stmt.body, body_context, index)

                if stmt.orelse:
                    else_context = _intersect_guards(
                        context, _negate_guard(guard_here)
                    )
                    # `elif` is represented as a single nested `If` in
                    # `orelse` -- recursing (rather than also recording
                    # a span for it here) lets that nested `If` record
                    # its own, further-composed span, and still reaches
                    # a real `else:` block at the end of the chain.
                    is_elif = len(stmt.orelse) == 1 and isinstance(
                        stmt.orelse[0], ast.If
                    )
                    if not is_elif:
                        else_span = _span(stmt.orelse)
                        if else_span:
                            index.version_guards.append(
                                (*else_span, else_context)
                            )
                    _walk_version_context(stmt.orelse, else_context, index)
            else:
                # Not a version test (implementation check, TYPE_CHECKING,
                # arbitrary condition, ...) -- the version context is
                # unaffected, but nested guards inside either branch
                # still need to inherit it.
                _walk_version_context(stmt.body, context, index)
                _walk_version_context(stmt.orelse, context, index)
        else:
            for child_list in _child_statement_lists(stmt):
                _walk_version_context(child_list, context, index)


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

    # Version guards get a dedicated recursive pass so nested/elif
    # chains compose correctly via interval intersection instead of
    # each `if` being considered in isolation (see
    # `_walk_version_context`).
    module_body = getattr(tree, "body", None)
    if module_body is not None:
        _walk_version_context(
            module_body,
            VersionGuard(min_version=None, max_version=None),
            index,
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test

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
            if (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            ):
                body_span = _span(node.body)
                if body_span:
                    index.type_checking_ranges.append(body_span)

        # --- try/except ImportError compatibility shims -------------
        if isinstance(node, ast.Try):
            has_import_error_handler = False
            for handler in node.handlers:
                handler_type = handler.type
                if (
                    handler_type is None
                    or (
                        isinstance(handler_type, ast.Name)
                        and handler_type.id in ("ImportError", "ModuleNotFoundError")
                    )
                    or (
                        isinstance(handler_type, ast.Tuple)
                        and any(
                            isinstance(e, ast.Name)
                            and e.id in ("ImportError", "ModuleNotFoundError")
                            for e in handler_type.elts
                        )
                    )
                ):
                    has_import_error_handler = True

            if has_import_error_handler:
                # Only import statements are part of the compatibility
                # shim. An unrelated statement inside the same try/except
                # must remain visible to compatibility rules.
                for statement in node.body:
                    if isinstance(statement, (ast.Import, ast.ImportFrom)):
                        statement_span = _span([statement])
                        if statement_span:
                            index.import_shim_ranges.append(statement_span)

                for handler in node.handlers:
                    for statement in handler.body:
                        if isinstance(
                            statement,
                            (ast.Import, ast.ImportFrom),
                        ):
                            statement_span = _span([statement])
                            if statement_span:
                                index.import_shim_ranges.append(statement_span)

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
        return (
            True,
            "inside a PyPy-only branch (sys.implementation.name == 'pypy'); never runs on CPython",
        )
    if finding_runtime == "pypy" and index.is_cpython_only(line):
        return True, "inside a CPython-only branch; never runs on PyPy"

    # Compatibility shims: only suppress pure API-availability
    # (compatibility) findings -- a shim doesn't neutralise a genuine
    # silent semantic difference, only an ImportError/AttributeError risk.
    if category == "compatibility" and index.is_import_shim(line):
        return True, "inside a try/except ImportError compatibility shim"

    # Version guards for compatibility (introduced/removed-API) findings.
    #
    # Correctness note (P0 fix, 2026-09 audit): a guard must only suppress
    # a finding when the guard's reachable version interval has NO overlap
    # with the finding's affected version interval. The previous logic
    # suppressed whenever `guard.min_version >= affected_from`, which is
    # wrong for findings with a bounded affected range: a guard of
    # `>= 3.15` does NOT neutralise a finding affected on `[3.15, 3.17)`,
    # it *guarantees* the code still runs squarely inside the affected
    # range. Suppression is only correct when the two intervals are
    # disjoint. See VersionGuard/interval reasoning below.
    if category == "compatibility" and (affected_from or affected_until):
        guard = index.version_guard_at(line)
        if guard is not None:
            from_tuple = _parse_version(affected_from) if affected_from else None
            until_tuple = _parse_version(affected_until) if affected_until else None

            # Finding interval: [finding_lo, finding_hi)
            finding_lo = from_tuple if from_tuple is not None else _NEG_INF
            finding_hi = until_tuple if until_tuple is not None else _POS_INF

            # Guard interval: [guard_lo, guard_hi) -- the version range for
            # which the guarded block actually executes.
            guard_lo = guard.min_version if guard.min_version is not None else _NEG_INF
            guard_hi = guard.max_version if guard.max_version is not None else _POS_INF

            # Disjoint intervals <=> no version can satisfy both at once.
            is_disjoint = guard_hi <= finding_lo or finding_hi <= guard_lo

            if is_disjoint:
                if guard_hi <= finding_lo:
                    # The guarded branch's whole reachable range ends at
                    # or before the affected window starts.
                    bound = guard.max_version
                    clause = (
                        f"`if sys.version_info < {bound}:`"
                        if bound is not None
                        else "this guard"
                    )
                    return True, (
                        f"inside {clause} which only runs entirely "
                        "before the affected version range"
                    )
                # Otherwise finding_hi <= guard_lo: the guarded branch's
                # whole reachable range starts at or after the affected
                # window ends.
                bound = guard.min_version
                clause = (
                    f"`if sys.version_info >= {bound}:`"
                    if bound is not None
                    else "this guard"
                )
                return True, (
                    f"inside {clause} which only runs entirely "
                    "after the affected version range"
                )

    return False, ""
