import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy069_asyncio_iscoroutinefunction import (
    AsyncioIscoroutinefunctionRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY069:
    rule = AsyncioIscoroutinefunctionRule()

    def test_detects_import(self):
        findings = run(self.rule, "from asyncio import iscoroutinefunction")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY069"
        assert findings[0].severity == Severity.WARNING

    def test_detects_call(self):
        findings = run(self.rule, "import asyncio\nasyncio.iscoroutinefunction(func)")
        assert len(findings) == 1

    def test_clean_inspect_iscoroutinefunction(self):
        findings = run(self.rule, "import inspect\ninspect.iscoroutinefunction(func)")
        assert len(findings) == 0

    def test_suggestion_mentions_inspect(self):
        findings = run(self.rule, "import asyncio\nasyncio.iscoroutinefunction(func)")
        assert "inspect" in findings[0].suggestion
