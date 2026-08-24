import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy004_tomllib import TomllibRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY004:
    rule = TomllibRule()

    def test_detects_import_tomllib(self):
        findings = run(self.rule, "import tomllib")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY004"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule, "from tomllib import loads")
        assert len(findings) == 1

    def test_clean_no_tomllib(self):
        findings = run(self.rule, "import json")
        assert len(findings) == 0

    def test_suggestion_mentions_tomli(self):
        findings = run(self.rule, "import tomllib")
        assert "tomli" in findings[0].suggestion.lower()