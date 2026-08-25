"""
PPY040 — subprocess.PIPE buffering differs on PyPy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
On CPython, subprocess.PIPE creates an OS pipe with predictable
buffering behaviour. On PyPy, due to GC timing differences, data
written to subprocess pipes may not be flushed to the child process
promptly, causing deadlocks or silent data loss when processes
communicate via stdin/stdout pipes.
"""
from __future__ import annotations

import ast

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity


class SubprocessPipeRule(BaseRule):
    rule_id = "PPY040"
    title   = "subprocess.PIPE buffering may cause deadlocks on PyPy"
    runtime = "pypy"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []
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
                                "On PyPy, GC timing differences can cause "
                                "subprocess pipe communication to deadlock "
                                "or lose data silently — especially when "
                                "both stdin and stdout use PIPE and the "
                                "buffers fill up before communicate() is called."
                            ),
                            severity=Severity.WARNING,
                            runtime=Runtime.PYPY,
                            suggestion=(
                                "Always use communicate() instead of "
                                "read()/write() directly on pipes. "
                                "communicate() handles buffering correctly "
                                "on both CPython and PyPy."
                            ),
                            docs_url=(
                                "https://docs.python.org/3/library/subprocess.html"
                                "#subprocess.Popen.communicate"
                            ),
                        ))
                        break
        return findings