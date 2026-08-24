import ast
import textwrap

from pyrift.finding import Runtime
from pyrift.rules.pypy.ppy001_gc_finalizer import GcFinalizerRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY001:
    rule = GcFinalizerRule()

    def test_detects_close_in_del(self):
        src = """
class MyResource:
    def __del__(self):
        self.file.close()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY001"
        assert findings[0].runtime == Runtime.PYPY

    def test_detects_flush_in_del(self):
        src = """
class MyResource:
    def __del__(self):
        self.conn.flush()
"""
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_clean_del_no_resource(self):
        src = """
class MyResource:
    def __del__(self):
        self.count -= 1
"""
        findings = run(self.rule, src)
        assert len(findings) == 0