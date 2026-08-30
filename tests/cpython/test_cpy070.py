import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy070_asyncio_event_loop_policy import (
    AsyncioEventLoopPolicyRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY070:
    rule = AsyncioEventLoopPolicyRule()

    def test_detects_get_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY070"
        assert findings[0].severity == Severity.WARNING

    def test_detects_set_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.set_event_loop_policy(policy)")
        assert len(findings) == 1

    def test_detects_default_event_loop_policy(self):
        findings = run(self.rule, "import asyncio\nasyncio.DefaultEventLoopPolicy")
        assert len(findings) == 1

    def test_clean_asyncio_run(self):
        findings = run(self.rule, "import asyncio\nasyncio.run(main())")
        assert len(findings) == 0

    def test_suggestion_mentions_asyncio_run(self):
        findings = run(self.rule, "import asyncio\nasyncio.get_event_loop_policy()")
        assert "asyncio.run" in findings[0].suggestion
