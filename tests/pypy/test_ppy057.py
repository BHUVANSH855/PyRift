"""Tests for PPY057 -- copyreg.dispatch_table / pickle.dispatch_table differs on PyPy."""
from __future__ import annotations

import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy057_copyreg_dispatch_table import CopyregDispatchTableRule

RULE = CopyregDispatchTableRule()
def parse(src): return ast.parse(textwrap.dedent(src))
def run(src): return RULE.check(parse(src), "<test>")

class TestPPY057:
    def test_copyreg_dispatch_table_assign(self):
        f = run("import copyreg\ncopyreg.dispatch_table[MyClass] = my_reducer\n")
        assert len(f) >= 1 and f[0].rule_id == "PPY057"

    def test_pickle_dispatch_table_assign(self):
        assert len(run("import pickle\npickle.dispatch_table = {}\n")) >= 1

    def test_dispatch_table_update(self):
        assert len(run("import copyreg\ncopyreg.dispatch_table.update({MyClass: my_reducer})\n")) >= 1

    def test_severity_is_warning(self):
        assert run("import copyreg\ncopyreg.dispatch_table[MyClass] = r\n")[0].severity == Severity.WARNING

    def test_suggestion_mentions_per_instance(self):
        assert "dispatch_table" in run("import copyreg\ncopyreg.dispatch_table[MyClass] = r\n")[0].suggestion

    def test_runtime_is_pypy(self):
        from pyrift.finding import Runtime
        assert run("import copyreg\ncopyreg.dispatch_table[MyClass] = r\n")[0].runtime == Runtime.PYPY

    def test_empty_file(self):
        assert run("") == []
