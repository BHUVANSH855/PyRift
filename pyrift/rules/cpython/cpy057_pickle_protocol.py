"""
CPY057 -- pickle default protocol changed to 5 in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.14 changed the default pickle protocol from 4 to 5.
Code that pickles data without an explicit non-None protocol
and shares it with older Python versions will silently fail.

Detects:
  - pickle.dumps(obj)              -- no protocol
  - pickle.dumps(obj, None)        -- None means default
  - pickle.dumps(obj, protocol=None) -- same
  - pickle.dump(obj, file)         -- no protocol
  - pickle.Pickler(file)           -- no protocol
  - pickle.Pickler(file, None)     -- None means default
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


def _is_none(node: ast.expr) -> bool:
    """Return True if node is the literal None."""
    return isinstance(node, ast.Constant) and node.value is None


def _has_explicit_protocol(keywords: list[ast.keyword],
                            positional_args: list[ast.expr],
                            protocol_pos: int) -> bool:
    """
    Return True only when a non-None protocol is specified.

    ``protocol_pos`` is the 0-based index of the protocol argument
    in the positional args list (1 for dumps, 2 for dump/Pickler).
    """
    # Check keyword argument
    for kw in keywords:
        if kw.arg == "protocol":
            return not _is_none(kw.value)

    # Check positional argument
    if len(positional_args) > protocol_pos:
        return not _is_none(positional_args[protocol_pos])

    return False


def _make_finding(filename: str, n: ast.Call,
                  api_name: str) -> Finding:
    return Finding(
        file=filename,
        line=n.lineno,
        col=n.col_offset,
        rule_id="CPY057",
        title="pickle default protocol changed to 5 in Python 3.14",
        description=(
            f"pickle.{api_name}() is called without an explicit non-None "
            "protocol= argument. Python 3.14 changed the default pickle "
            "protocol from 4 to 5. Data pickled with the default on 3.14+ "
            "cannot be unpickled by Python 3.7 or below. Passing "
            "protocol=None is equivalent to omitting it."
        ),
        severity=Severity.WARNING,
        runtime=Runtime.CPYTHON,
        affected_from="3.14",
        suggestion=(
            "Specify the protocol explicitly for cross-version "
            "compatibility: pickle.dumps(obj, protocol=4) for "
            "Python 3.4+ compatibility, or protocol=2 for maximum "
            "compatibility. Use pickle.HIGHEST_PROTOCOL only when "
            "cross-version compatibility is not required."
        ),
        docs_url=(
            "https://docs.python.org/3/library/pickle.html"
            "#pickle-protocols"
        ),
    )


class PickleProtocolRule(BaseRule):
    rule_id = "CPY057"
    title = "pickle default protocol changed to 5 in Python 3.14"
    runtime = "cpython"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue

            func = n.func
            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "pickle"
            ):
                continue

            api = func.attr

            if api in ("dumps",):
                # pickle.dumps(obj, protocol, ...)
                # protocol is the 2nd argument (index 1)
                if not _has_explicit_protocol(n.keywords, n.args, 1):
                    findings.append(_make_finding(filename, n, api))

            elif api in ("dump",):
                # pickle.dump(obj, file, protocol, ...)
                # protocol is the 3rd argument (index 2)
                if not _has_explicit_protocol(n.keywords, n.args, 2):
                    findings.append(_make_finding(filename, n, api))

            elif api in ("Pickler",) and not _has_explicit_protocol(n.keywords, n.args, 1):
                # pickle.Pickler(file, protocol, ...)
                # protocol is the 2nd argument (index 1)
                findings.append(_make_finding(filename, n, api))

        return findings