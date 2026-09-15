import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy019_distutils import DistutilsRule


def parse(src):
    return ast.parse(textwrap.dedent(src))


def run(rule, src):
    return rule.check(parse(src), "<test>")


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

    def test_detects_distutils_config(self):
        findings = run(
            self.rule,
            "from distutils.config import PyPIRCCommand",
        )
        assert len(findings) == 1

    def test_detects_distutils_nested_submodule(self):
        findings = run(
            self.rule,
            "from distutils.command.build_ext import build_ext",
        )
        assert len(findings) == 1

    def test_clean_setuptools(self):
        findings = run(self.rule, "from setuptools import setup")
        assert len(findings) == 0

    def test_clean_other_standard_library_module(self):
        findings = run(self.rule, "import sys")
        assert findings == []

    def test_ignores_similarly_named_module(self):
        findings = run(
            self.rule,
            "from my_distutils import setup",
        )
        assert findings == []

    def test_detects_multiple_distutils_imports(self):
        findings = run(
            self.rule,
            "import distutils\nfrom distutils.version import StrictVersion\n",
        )
        assert len(findings) == 2

    def test_detects_function_local_import(self):
        findings = run(
            self.rule,
            "def f():\n    import distutils\n",
        )
        assert len(findings) == 1

    def test_detects_distutils_inside_pre_312_version_guard(self):
        findings = run(
            self.rule,
            "import sys\nif sys.version_info < (3, 12):\n    import distutils\n",
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY019"

    def test_detects_distutils_inside_312_plus_version_guard(self):
        findings = run(
            self.rule,
            "import sys\nif sys.version_info >= (3, 12):\n    import distutils\n",
        )
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY019"

    def test_detects_insufficient_version_guard(self):
        findings = run(
            self.rule,
            "import sys\nif sys.version_info >= (3, 10):\n    import distutils\n",
        )
        assert len(findings) == 1

    def test_suggestion_identifies_specific_replacements(self):
        findings = run(
            self.rule,
            "import distutils",
        )
        suggestion = findings[0].suggestion.lower()

        assert "setuptools" in suggestion
        assert "packaging" in suggestion
        assert "shutil.which" in suggestion
        assert "sysconfig" in suggestion

    def test_docs_url_points_to_pep_632(self):
        findings = run(self.rule, "import distutils")
        assert findings[0].docs_url == "https://peps.python.org/pep-0632/"
