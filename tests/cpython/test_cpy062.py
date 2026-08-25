import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy062_template_string import TemplateStringRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY062:
    rule = TemplateStringRule()

    def test_detects_import_templatelib(self):
        findings = run(self.rule, "import string.templatelib")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY062"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule,
            "from string.templatelib import Template")
        assert len(findings) == 1

    def test_clean_string_import(self):
        findings = run(self.rule, "import string")
        assert len(findings) == 0

    def test_suggestion_mentions_version(self):
        findings = run(self.rule, "import string.templatelib")
        assert "3, 14" in findings[0].suggestion or \
               "3.14" in findings[0].suggestion