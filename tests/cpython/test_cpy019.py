import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy019_distutils import DistutilsRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY019:
    rule = DistutilsRule()

    def test_detects_distutils_import(self):
        findings = run(self.rule, "import distutils")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY019"
        assert findings[0].severity == Severity.ERROR

    def test_detects_distutils_submodule(self):
        findings = run(self.rule, "from distutils.core import setup")
        assert len(findings) == 1

    def test_detects_distutils_version(self):
        findings = run(self.rule, "import distutils.version")
        assert len(findings) == 1

    def test_clean_setuptools(self):
        findings = run(self.rule, "from setuptools import setup")
        assert len(findings) == 0

    def test_suggestion_mentions_setuptools(self):
        findings = run(self.rule, "import distutils")
        assert "setuptools" in findings[0].suggestion.lower()