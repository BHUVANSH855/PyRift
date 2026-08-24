import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy021_asyncio_coroutine import AsyncioIsCoroutineRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY021:
    rule = AsyncioIsCoroutineRule()

    def test_detects_asyncio_iscoroutinefunction(self):
        findings = run(self.rule, "import asyncio\nasyncio.iscoroutinefunction(fn)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY021"
        assert findings[0].severity == Severity.WARNING

    def test_clean_inspect_version(self):
        findings = run(self.rule, "import inspect\ninspect.iscoroutinefunction(fn)")
        assert len(findings) == 0

    def test_suggestion_mentions_inspect(self):
        findings = run(self.rule, "asyncio.iscoroutinefunction(fn)")
        assert "inspect" in findings[0].suggestion.lower()