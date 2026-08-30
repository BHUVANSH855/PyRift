import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy052_importlib_abc import ImportlibAbcPyPyRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY052:
    rule = ImportlibAbcPyPyRule()

    def test_detects_resource_reader(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY052"
        assert findings[0].severity == Severity.INFO

    def test_detects_traversable_resources(self):
        findings = run(self.rule, "from importlib.abc import TraversableResources")
        assert len(findings) == 1

    def test_clean_importlib_resources_abc(self):
        findings = run(self.rule, "from importlib.resources.abc import TraversableResources")
        assert len(findings) == 0

    def test_suggestion_mentions_testing(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert "test" in findings[0].suggestion.lower() or "cpython" in findings[0].suggestion.lower()
