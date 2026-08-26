import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy040_graphlib import GraphlibRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY040:
    rule = GraphlibRule()

    def test_detects_import_graphlib(self):
        findings = run(self.rule, "import graphlib")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY040"
        assert findings[0].severity == Severity.ERROR

    def test_detects_from_import(self):
        findings = run(self.rule, "from graphlib import TopologicalSorter")
        assert len(findings) == 1

    def test_clean_other_import(self):
        findings = run(self.rule, "import networkx")
        assert len(findings) == 0

    def test_suggestion_mentions_version(self):
        findings = run(self.rule, "import graphlib")
        assert "3, 9" in findings[0].suggestion or \
               "3.9" in findings[0].suggestion or \
               "backport" in findings[0].suggestion.lower()