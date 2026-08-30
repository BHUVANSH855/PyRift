import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy049_gc_behavior import GcBehaviorRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


class TestPPY049:
    rule = GcBehaviorRule()

    def test_detects_gc_collect(self):
        findings = run(self.rule, "import gc\ngc.collect()")

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"
        assert findings[0].severity == Severity.WARNING

    def test_detects_gc_get_objects(self):
        findings = run(self.rule, "import gc\ngc.get_objects()")

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"

    def test_detects_gc_disable(self):
        findings = run(self.rule, "import gc\ngc.disable()")

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"

    def test_detects_gc_enable(self):
        findings = run(self.rule, "import gc\ngc.enable()")

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"

    def test_does_not_detect_unrelated_module(self):
        findings = run(self.rule, "import os\nos.collect()")

        assert len(findings) == 0

    def test_does_not_detect_gc_attribute_reference(self):
        findings = run(self.rule, "import gc\ncollector = gc.collect")

        assert len(findings) == 0

    def test_does_not_detect_unrelated_gc_function(self):
        findings = run(self.rule, "import gc\ngc.get_threshold()")

        assert len(findings) == 0

    def test_suggestion_mentions_cleanup(self):
        findings = run(self.rule, "import gc\ngc.collect()")

        suggestion = findings[0].suggestion.lower()

        assert "context" in suggestion or "explicit" in suggestion