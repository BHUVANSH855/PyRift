import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy048_concurrent_interpreters import (
    ConcurrentInterpretersRule,
)


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY048:
    rule = ConcurrentInterpretersRule()

    def test_detects_import(self):
        findings = run(self.rule, "import concurrent.interpreters")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY048"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule,
            "from concurrent.interpreters import Interpreter")
        assert len(findings) == 1

    def test_clean_concurrent_futures(self):
        findings = run(self.rule,
            "from concurrent.futures import ThreadPoolExecutor")
        assert len(findings) == 0

    def test_suggestion_mentions_version(self):
        findings = run(self.rule, "import concurrent.interpreters")
        assert "3, 14" in findings[0].suggestion or \
               "3.14" in findings[0].suggestion