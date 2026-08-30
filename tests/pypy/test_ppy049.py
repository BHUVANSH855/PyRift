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
        findings = run(
            self.rule,
            "import gc\ngc.collect()",
        )

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

    def test_detects_gc_collect_import_alias(self):
        findings = run(
            self.rule,
            "import gc as garbage\ngarbage.collect()",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"
        assert findings[0].severity == Severity.WARNING

    def test_does_not_detect_shadowed_gc_name(self):
        findings = run(
            self.rule,
            "gc = object()\ngc.collect()",
        )

        assert len(findings) == 0

    def test_does_not_detect_non_gc_import_aliased_as_gc(self):
        findings = run(
            self.rule,
            "import other as gc\ngc.collect()",
        )

        assert len(findings) == 0

    def test_suggestion_mentions_cleanup(self):
        findings = run(
            self.rule,
            "import gc\ngc.get_objects()",
        )

        assert len(findings) == 1
        suggestion = findings[0].suggestion.lower()

        assert "context" in suggestion or "explicit" in suggestion

    def test_does_not_detect_gc_shadowed_inside_function(self):
        findings = run(
            self.rule,
            "import gc\n"
            "def safe():\n"
            "    gc = object()\n"
            "    gc.collect()\n",
        )

        assert len(findings) == 0

    def test_does_not_detect_non_gc_import_inside_function(self):
        findings = run(
            self.rule,
            "import gc\n"
            "def safe():\n"
            "    import other as gc\n"
            "    gc.collect()\n",
        )

        assert len(findings) == 0

    def test_detects_gc_imported_inside_function(self):
        findings = run(
            self.rule,
            "def collect_safely():\n"
            "    import gc\n"
            "    gc.collect()\n",
        )

        assert len(findings) == 1
        assert findings[0].rule_id == "PPY049"

    def test_does_not_leak_gc_binding_into_nested_function(self):
        findings = run(
            self.rule,
            "import gc\n"
            "def outer():\n"
            "    def inner():\n"
            "        gc = object()\n"
            "        gc.collect()\n"
            "    inner()\n",
        )

        assert len(findings) == 0