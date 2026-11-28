"""Tests for PPY055 -- sys.setprofile() / sys.getprofile() not reliably supported on PyPy."""
from __future__ import annotations

import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy055_sys_setprofile import SysSetprofileRule

RULE = SysSetprofileRule()
def parse(src): return ast.parse(textwrap.dedent(src))
def run(src): return RULE.check(parse(src), "<test>")

class TestPPY055:
    def test_setprofile(self):
        f = run("import sys\nsys.setprofile(my_profiler)\n")
        assert len(f) == 1 and f[0].rule_id == "PPY055"

    def test_getprofile(self):
        f = run("import sys\nf = sys.getprofile()\n")
        assert len(f) == 1 and f[0].rule_id == "PPY055"

    def test_severity_is_warning(self):
        assert run("import sys\nsys.setprofile(my_profiler)\n")[0].severity == Severity.WARNING

    def test_suggestion_mentions_vmprof(self):
        assert "vmprof" in run("import sys\nsys.setprofile(my_profiler)\n")[0].suggestion.lower()

    def test_aliased_sys(self):
        assert len(run("import sys as s\ns.setprofile(None)\n")) == 1

    def test_runtime_is_pypy(self):
        from pyrift.finding import Runtime
        assert run("import sys\nsys.setprofile(None)\n")[0].runtime == Runtime.PYPY

    def test_sys_settrace_not_flagged(self):
        assert run("import sys\nsys.settrace(None)\n") == []

    def test_empty_file(self):
        assert run("") == []
