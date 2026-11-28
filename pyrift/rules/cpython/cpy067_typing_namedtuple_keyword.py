"""
CPY067 -- typing.NamedTuple keyword-argument syntax deprecated (3.13),
          removed in Python 3.15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The undocumented keyword-argument form of ``typing.NamedTuple`` was deprecated
in Python 3.13 and removed in Python 3.15.  On 3.13 and 3.14 it emits a
``DeprecationWarning``; on 3.15+ it raises a ``TypeError`` immediately.

**Broken (deprecated 3.13, TypeError on 3.15+):**

    from typing import NamedTuple

    Point = NamedTuple("Point", x=int, y=int)   # keyword fields → broken

**Valid alternatives (unchanged):**

    # Class-based syntax (preferred):
    class Point(NamedTuple):
        x: int
        y: int

    # Functional list-of-tuples syntax:
    Point = NamedTuple("Point", [("x", int), ("y", int)])

    # Empty class (zero fields):
    class Empty(NamedTuple):
        pass

**History / evidence:**

* Deprecated in 3.13 — CPython gh-105566, PR #105609 (commit ad56340b).
  DeprecationWarning message:
  "Creating NamedTuple classes using keyword arguments is deprecated
   and will be disallowed in Python 3.15. Use the class-based or
   functional syntax instead."
* Removed in 3.15 — CPython gh-133817, commit c5e1775825.
  New signature: ``def NamedTuple(typename, fields, /)``
  (both parameters are positional-only; any keyword argument now raises
  ``TypeError: NamedTuple() got an unexpected keyword argument '<name>'``).
* Python 3.15 What's New (Removed section), Python 3.14 typing docs:
  "deprecated-removed:: 3.13 3.15"
* ``typing_extensions`` >= 4.7.0 mirrors the same deprecation.
* Precedent: TypedDict keyword-field form deprecated 3.11, removed 3.13.

**What is NOT deprecated:**

* ``NamedTuple("Point", [("x", int)])``  — list-of-tuples form (always valid)
* ``NamedTuple("Point", {"x": int})``    — 2-arg dict form (not documented,
  not deprecated either; the new positional-only signature accepts it because
  the second positional argument is ``fields`` and dicts are iterable)
* Class-based syntax                     — preferred and unchanged
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig

# Module names whose NamedTuple is subject to this deprecation.
# typing_extensions >= 4.7.0 mirrors the same deprecation warning.
_TYPING_MODULES = frozenset({"typing", "typing_extensions"})


def _is_namedtuple_call(func: ast.expr) -> bool:
    """Return True if *func* is a bare or qualified NamedTuple reference."""
    if isinstance(func, ast.Name):
        return func.id == "NamedTuple"
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "NamedTuple"
        and isinstance(func.value, ast.Name)
        and func.value.id in _TYPING_MODULES
    )


class TypingNamedTupleKeywordRule(BaseRule):
    rule_id = "CPY067"
    title = "typing.NamedTuple keyword syntax deprecated in 3.13, removed in 3.15"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            if not _is_namedtuple_call(n.func):
                continue
            # Must have at least the typename positional argument.
            if not n.args:
                continue

            # Only flag keyword-argument field form:
            #   NamedTuple("Point", x=int, y=int)
            # Exclude **kwargs unpacking (kw.arg is None).
            # The list-of-tuples form and the 2-arg dict form are NOT flagged.
            keyword_fields = [kw for kw in n.keywords if kw.arg is not None]
            if not keyword_fields:
                continue

            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "The keyword-argument form of NamedTuple — e.g. "
                    "NamedTuple('Point', x=int, y=int) — was deprecated "
                    "in Python 3.13 and removed in Python 3.15. "
                    "On Python 3.13–3.14 it emits a DeprecationWarning; "
                    "on Python 3.15+ it raises TypeError immediately. "
                    "(CPython gh-105566 / gh-133817)"
                ),
                severity=Severity.ERROR,
                runtime=Runtime.CPYTHON,
                affected_from="3.13",
                suggestion=(
                    "Use the class-based syntax (preferred):\n"
                    "  class Point(NamedTuple):\n"
                    "      x: int\n"
                    "      y: int\n"
                    "Or the list-of-tuples functional syntax:\n"
                    "  Point = NamedTuple('Point', [('x', int), ('y', int)])"
                ),
                docs_url=(
                    "https://docs.python.org/3/whatsnew/3.15.html#removed"
                ),
            ))

        return findings
