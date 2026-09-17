"""
PPY040 — subprocess.PIPE deadlock risk (verify: not actually PyPy-specific)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Correction (2026-09 audit, verified against current official docs): the
original version of this rule attributed subprocess.PIPE deadlocks to
"GC timing differences" on PyPy. That causal claim does not hold up --
Python's own subprocess documentation attributes this deadlock entirely
to fixed-size OS pipe buffers filling up ("Use communicate() rather
than .stdin.write, .stdout.read or .stderr.read to avoid deadlocks due
to any of the other OS pipe buffers filling up and blocking the child
process"), and this applies identically on CPython and PyPy -- it is
not an implementation difference at all, just a universal subprocess
gotcha. Framing it as a PyPy-specific "GC timing" issue was inaccurate
and risked teaching people the wrong mental model of the actual
mechanism.

The rule is kept (using communicate() instead of raw
stdin.write()/stdout.read() is still good, portable advice worth
flagging), but the title, description, and evidence now correctly
describe it as a universal Python gotcha rather than a PyPy
implementation difference.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Confidence, Finding, Runtime, Severity
from pyrift.targets import TargetConfig


class SubprocessPipeRule(BaseRule):
    rule_id = "PPY040"
    title   = "subprocess Popen(...PIPE) without communicate() risks deadlock"
    runtime = "pypy"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []

        # Conservative false-positive guard (audit fix): if `.communicate(`
        # is called anywhere in this module, don't flag any Popen(PIPE=...)
        # site. This can't prove the communicate() call targets the same
        # Popen object without real data-flow analysis, but the previous
        # version flagged code unconditionally -- including code that
        # already calls communicate() correctly, which is exactly the fix
        # this rule recommends. Erring toward not flagging matches
        # PyRift's stated preference for false negatives over false
        # positives.
        has_communicate_call = any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "communicate"
            for n in ast.walk(node)
        )
        if has_communicate_call:
            return findings

        for n in ast.walk(node):
            if not isinstance(n, ast.Call):
                continue
            func = n.func
            is_popen = False
            if isinstance(func, ast.Name) and func.id == "Popen" or (isinstance(func, ast.Attribute) and
                  func.attr == "Popen"):
                is_popen = True
            if not is_popen:
                continue
            # Check if stdout=PIPE or stdin=PIPE
            for kw in n.keywords:
                if (
                    kw.arg in ("stdout", "stdin", "stderr")
                    and isinstance(kw.value, ast.Attribute)
                    and kw.value.attr == "PIPE"
                ):
                        findings.append(Finding(
                            file=filename,
                            line=n.lineno,
                            col=n.col_offset,
                            rule_id=self.rule_id,
                            title=self.title,
                            description=(
                                f"Popen is called with {kw.arg}=PIPE. "
                                "Always use communicate() to read from "
                                "subprocess pipes: reading/writing "
                                "directly with .stdin.write()/"
                                ".stdout.read() can deadlock as soon as "
                                "a fixed-size OS pipe buffer fills up "
                                "and blocks the child process -- this "
                                "is a general Python/OS-level gotcha "
                                "documented in Python's own subprocess "
                                "docs, and applies identically on "
                                "CPython and PyPy. It is not a PyPy "
                                "implementation difference."
                            ),
                            severity=Severity.WARNING,
                            confidence=Confidence.HIGH,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "Always use communicate() instead of "
                                "read()/write() directly on pipes. "
                                "communicate() handles buffering "
                                "correctly on both CPython and PyPy."
                            ),
                            docs_url=(
                                "https://docs.python.org/3/library/subprocess.html"
                                "#subprocess.Popen.communicate"
                            ),
                        ))
                        break
        return findings