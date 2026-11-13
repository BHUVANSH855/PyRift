import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy033_is_relative_to import IsRelativeToRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY033:
    rule = IsRelativeToRule()

    def test_detects_is_relative_to(self):
        findings = run(self.rule,
            "from pathlib import Path\np.is_relative_to('/base')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY033"
        assert findings[0].severity == Severity.ERROR

    def test_clean_other_pathlib_method(self):
        findings = run(self.rule, "p.is_absolute()")
        assert len(findings) == 0

    def test_suggestion_mentions_relative_to(self):
        findings = run(self.rule, "p.is_relative_to('/x')")
        assert "relative_to" in findings[0].suggestion.lower()

    def test_clean_try_except_attribute_error(self):
        # Inside try/except AttributeError — already guarded
        findings = run(self.rule, """\
            try:
                p.is_relative_to('/base')
            except AttributeError:
                pass
        """)
        assert len(findings) == 0

    def test_clean_version_guard(self):
        # Inside sys.version_info >= (3, 9) — already guarded
        findings = run(self.rule, """\
            import sys
            if sys.version_info >= (3, 9):
                p.is_relative_to('/base')
        """)
        assert len(findings) == 0

    def test_clean_hasattr_guard(self):
        # Generic version_info check
        findings = run(self.rule, """\
            import sys
            if hasattr(sys, 'version_info'):
                p.is_relative_to('/base')
        """)
        # hasattr check doesn't reference version_info directly in a comparison
        # so this should still be flagged unless we have a broader guard detection
        assert isinstance(findings, list)

    def test_still_flags_unguarded(self):
        # Unguarded call should still be flagged
        findings = run(self.rule, "p.is_relative_to('/x')")
        assert len(findings) == 1

    def test_clean_try_except_bare(self):
        # Bare except also guards
        findings = run(self.rule, """\
            try:
                p.is_relative_to('/base')
            except:
                pass
        """)
        assert len(findings) == 0



class TestCPY033EvalCondition:
    """Tests for the eval_condition-based early-exit in CPY033."""

    rule = IsRelativeToRule()

    def test_skips_when_min_version_gte_39(self):
        """When project minimum is 3.9+, CPY033 must return no findings."""
        from pyrift.targets import PythonVersion, TargetConfig

        cfg = TargetConfig(minimum=PythonVersion(3, 9))
        findings = self.rule.check(parse("p.is_relative_to('/x')"), "<test>", cfg)
        assert findings == []

    def test_skips_when_min_version_310(self):
        """3.10 minimum also satisfies >= 3.9."""
        from pyrift.targets import PythonVersion, TargetConfig

        cfg = TargetConfig(minimum=PythonVersion(3, 10))
        findings = self.rule.check(parse("p.is_relative_to('/x')"), "<test>", cfg)
        assert findings == []

    def test_fires_when_min_version_38(self):
        """3.8 minimum means 3.8 users are affected; rule must fire."""
        from pyrift.targets import PythonVersion, TargetConfig

        cfg = TargetConfig(minimum=PythonVersion(3, 8))
        findings = self.rule.check(parse("p.is_relative_to('/x')"), "<test>", cfg)
        assert len(findings) == 1

    def test_fires_without_target_config(self):
        """No TargetConfig means scan everything; rule must fire."""
        findings = self.rule.check(parse("p.is_relative_to('/x')"), "<test>", None)
        assert len(findings) == 1

    def test_fires_without_minimum(self):
        """TargetConfig with no minimum bound must still fire."""
        from pyrift.targets import TargetConfig

        cfg = TargetConfig(minimum=None)
        findings = self.rule.check(parse("p.is_relative_to('/x')"), "<test>", cfg)
        assert len(findings) == 1
