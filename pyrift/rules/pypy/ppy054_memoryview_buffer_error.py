"""
PPY054 -- memoryview holds live buffer; bytearray/BytesIO resize raises BufferError
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, resizing a ``bytearray`` or ``io.BytesIO`` while an active
``memoryview`` refers to it raises ``BufferError``.  On PyPy, the GC model
means memoryviews may not be released when they go out of scope in the same
deterministic way, so the BufferError can fire in places that work fine on
CPython simply because on CPython the view has been collected already.

The inverse also happens: code that expects a view over a ``bytearray`` to
*prevent* a resize (relying on the BufferError as a guard) may not get that
protection on PyPy if the view has been collected by the GC before the resize.

Both patterns produce silent wrong results or unexpected exceptions depending
on the GC scheduling of the runtime.

Documentation:
  https://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class MemoryviewBufferErrorRule(BaseRule):
    rule_id = "PPY054"
    title = "memoryview over bytearray/BytesIO resize behaviour differs on PyPy"
    runtime = "pypy"
    severity = Severity.WARNING

    def _is_memoryview_call(self, node: ast.AST) -> bool:
        """Return True when node looks like memoryview(...)."""
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "memoryview"
        )

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for n in ast.walk(node):
            if not self._is_memoryview_call(n):
                continue
            # Fire on any memoryview() call — the GC timing issue applies
            # to all such uses, but limit noise by only flagging when the
            # argument is a bare Name (variable) rather than a literal.
            assert isinstance(n, ast.Call)
            call: ast.Call = n
            if call.args and isinstance(call.args[0], ast.Name):
                findings.append(Finding(
                    file=filename,
                    line=call.lineno,
                    col=call.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description=(
                        "memoryview() pins the underlying buffer and prevents "
                        "resizing a bytearray or BytesIO while the view is "
                        "alive. On PyPy, GC timing differs from CPython's "
                        "reference counting: a memoryview may be collected "
                        "earlier or later than expected, causing a BufferError "
                        "to fire at a different point than on CPython (or not "
                        "at all when you expect the view to still be active)."
                    ),
                    severity=Severity.WARNING,
                    runtime=Runtime.PYPY,
                    suggestion=(
                        "Use an explicit 'with memoryview(buf) as mv:' block "
                        "or call mv.release() explicitly to ensure the view is "
                        "released before resizing. This makes GC-timing "
                        "differences irrelevant."
                    ),
                    docs_url=(
                        "https://doc.pypy.org/en/latest/cpython_differences.html"
                        "#differences-related-to-garbage-collection-strategies"
                    ),
                ))
        return findings