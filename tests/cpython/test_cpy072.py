import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy072_importlib_abc_resource import ImportlibAbcResourceRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY072:
    rule = ImportlibAbcResourceRule()

    def test_detects_resource_reader_import(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY072"
        assert findings[0].severity == Severity.ERROR

    def test_detects_traversable_resources_import(self):
        findings = run(self.rule, "from importlib.abc import TraversableResources")
        assert len(findings) == 1

    def test_detects_resource_contents_import(self):
        findings = run(self.rule, "from importlib.abc import ResourceContents")
        assert len(findings) == 1

    def test_clean_importlib_resources_abc(self):
        findings = run(self.rule, "from importlib.resources.abc import TraversableResources")
        assert len(findings) == 0

    def test_suggestion_mentions_resources_abc(self):
        findings = run(self.rule, "from importlib.abc import ResourceReader")
        assert "importlib.resources.abc" in findings[0].suggestion
