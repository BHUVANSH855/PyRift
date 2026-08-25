"""
CPY057 — pickle default protocol changed to 5 in Python 3.14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python 3.14 changed the default pickle protocol from 4 to 5.
Data pickled with Python 3.14+ using the default protocol cannot
be unpickled by Python 3.7 or below (protocol 5 requires 3.8+).

Code that pickles data without an explicit protocol= argument and
shares it with older Python versions will silently fail to load.
"""

from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


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

            is_pickle_dump = (
                isinstance(func, ast.Attribute)
                and func.attr in ("dumps", "dump")
                and isinstance(func.value, ast.Name)
                and func.value.id == "pickle"
            )

            if not is_pickle_dump:
                continue

            has_protocol = any(
                kw.arg == "protocol"
                for kw in n.keywords
            )

            if func.attr == "dump":
                # pickle.dump(obj, file, protocol)
                # The third positional argument is protocol.
                has_positional_protocol = len(n.args) >= 3
            else:
                # pickle.dumps(obj, protocol)
                # The second positional argument is protocol.
                has_positional_protocol = len(n.args) >= 2

            if has_protocol or has_positional_protocol:
                continue

            findings.append(
                Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        f"pickle.{func.attr}() is called without an explicit "
                        "protocol= argument. Python 3.14 changed the default "
                        "pickle protocol from 4 to 5. Data pickled with the "
                        "default on 3.14+ cannot be unpickled by Python 3.7 "
                        "or below. This silently causes "
                        "'ValueError: unsupported pickle protocol: 5' "
                        "on older Python versions."
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
            )

        return findings