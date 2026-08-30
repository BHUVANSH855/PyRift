import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy066_asyncio_child_watcher import AsyncioChildWatcherRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY066:
    rule = AsyncioChildWatcherRule()

    def test_detects_threaded_child_watcher_import(self):
        findings = run(self.rule, "from asyncio import ThreadedChildWatcher")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY066"
        assert findings[0].severity == Severity.ERROR

    def test_detects_fast_child_watcher(self):
        findings = run(self.rule, "from asyncio import FastChildWatcher")
        assert len(findings) == 1

    def test_detects_multi_loop_child_watcher(self):
        findings = run(self.rule, "from asyncio import MultiLoopChildWatcher")
        assert len(findings) == 1

    def test_detects_safe_child_watcher(self):
        findings = run(self.rule, "from asyncio import SafeChildWatcher")
        assert len(findings) == 1

    def test_detects_usage_pattern(self):
        findings = run(self.rule, "ThreadedChildWatcher()")
        assert len(findings) >= 1

    def test_clean_asyncio_runner(self):
        findings = run(self.rule, "import asyncio\nasyncio.Runner")
        assert len(findings) == 0

    def test_suggestion_mentions_pidfd(self):
        findings = run(self.rule, "from asyncio import ThreadedChildWatcher")
        assert "PIDFD" in findings[0].suggestion or "Runner" in findings[0].suggestion
