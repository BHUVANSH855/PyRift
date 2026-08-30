import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy049_gc_behavior import GcBehaviorRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY049:
    rule = GcBehaviorRule()

    def test_detects_gc_get_objects(self):
        findings = run(self.rule, "import gc\ngc.get_objects()")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"
        assert findings[0].severity == Severity.WARNING

    def test_detects_gc_get_count(self):
        findings = run(self.rule, "import gc\ngc.get_count()")
        assert len(findings) == 1

    def test_detects_gc_disable(self):
        findings = run(self.rule, "import gc\ngc.disable()")
        assert len(findings) == 1

    def test_detects_gc_enable(self):
        findings = run(self.rule, "import gc\ngc.enable()")
        assert len(findings) == 1

    def test_clean_other_module(self):
        findings = run(self.rule, "import os\nos.collect()")
        assert len(findings) == 0

    def test_suggestion_mentions_context_managers(self):
        findings = run(self.rule, "import gc\ngc.get_objects()")
        assert "context" in findings[0].suggestion.lower() or "explicit" in findings[0].suggestion.lower()
