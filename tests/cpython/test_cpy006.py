import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy006_asyncio_timeout import AsyncioTimeoutRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY006:
    rule = AsyncioTimeoutRule()

    def test_detects_asyncio_timeout(self):
        findings = run(self.rule, "async with asyncio.timeout(5): pass")
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY006"

    def test_detects_taskgroup(self):
        findings = run(self.rule, "async with asyncio.TaskGroup() as tg: pass")
        assert len(findings) >= 1

    def test_clean_asyncio_sleep(self):
        findings = run(self.rule, "await asyncio.sleep(1)")
        assert len(findings) == 0