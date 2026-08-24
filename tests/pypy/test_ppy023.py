import ast
import textwrap

from pyrift.rules.pypy.ppy023_inspect_ismethod import InspectIsMethodRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY023:
    rule = InspectIsMethodRule()

    def test_detects_inspect_ismethod(self):
        findings = run(self.rule,
            "import inspect\ninspect.ismethod([].__add__)")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY023"

    def test_clean_inspect_isfunction(self):
        findings = run(self.rule,
            "import inspect\ninspect.isfunction(fn)")
        assert len(findings) == 0

    def test_suggestion_mentions_callable(self):
        findings = run(self.rule, "inspect.ismethod(fn)")
        assert "callable" in findings[0].suggestion.lower()