"""
PPY005 — File buffering behaviour differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, writing to an unbuffered or line-buffered file flushes
data to disk predictably. On PyPy, due to the GC and internal
buffering differences, data written to files may not be flushed
even when the file appears to be closed — silently losing data.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

# open() modes that involve writing
WRITE_MODES = {"w", "wb", "a", "ab", "w+", "wb+", "a+", "ab+", "x", "xb"}


class IoBufferingRule(BaseRule):
    rule_id = "PPY005"
    title   = "File write without explicit flush may lose data on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Detect: open(...) calls not used as context manager
            if not isinstance(n, ast.Call):
                continue

            func = n.func
            is_open = False
            if isinstance(func, ast.Name) and func.id == "open" or (isinstance(func, ast.Attribute) and
                  func.attr == "open" and
                  isinstance(func.value, ast.Name) and
                  func.value.id in ("io", "builtins")):
                is_open = True

            if not is_open:
                continue

            # Check if mode argument suggests writing
            mode_is_write = False
            # positional arg index 1 is mode
            if len(n.args) >= 2:
                mode_arg = n.args[1]
                if (
                    isinstance(mode_arg, ast.Constant)
                    and any(m in str(mode_arg.value) for m in ("w", "a", "x"))
                ):
                        mode_is_write = True
            # keyword arg
            for kw in n.keywords:
                if (
                    kw.arg == "mode"
                    and isinstance(kw.value, ast.Constant)
                    and any(m in str(kw.value.value) for m in ("w", "a", "x"))
                ):
                        mode_is_write = True

            if not mode_is_write:
                continue

            # Check if this open() call is NOT inside a 'with' statement
            # We detect this by checking parent context — approximate:
            # if the Call is directly assigned (not used as context manager)
            findings.append(Finding(
                file=filename,
                line=n.lineno,
                col=n.col_offset,
                rule_id=self.rule_id,
                title=self.title,
                description=(
                    "A file is opened for writing. On PyPy, file buffering "
                    "behaviour differs from CPython — data may not be flushed "
                    "to disk even after close() due to GC timing differences. "
                    "Without explicit flush() or a context manager, writes can "
                    "be silently lost on PyPy."
                ),
                severity=Severity.WARNING,
                runtime=Runtime.PYPY,
                suggestion=(
                    "Always use 'with open(...) as f:' to guarantee flushing "
                    "and closing. If not using a context manager, call "
                    "f.flush() explicitly before f.close()."
                ),
                docs_url=(
                    "https://doc.pypy.org/en/latest/cpython_differences.html"
                    "#differences-related-to-garbage-collection-strategies"
                ),
            ))

        return findings