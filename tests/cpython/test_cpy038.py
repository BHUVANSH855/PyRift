import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy038_asyncio_get_event_loop import AsyncioGetEventLoopRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY038:
    rule = AsyncioGetEventLoopRule()

    def test_detects_get_event_loop(self):
        findings = run(self.rule,
            "import asyncio\nloop = asyncio.get_event_loop()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY038"
        assert findings[0].severity == Severity.ERROR

    def test_clean_asyncio_run(self):
        findings = run(self.rule,
            "import asyncio\nasyncio.run(main())")
        assert len(findings) == 0

    def test_suggestion_mentions_asyncio_run(self):
        findings = run(self.rule, "asyncio.get_event_loop()")
        assert "asyncio.run" in findings[0].suggestion.lower() or \
               "run" in findings[0].suggestion.lower()