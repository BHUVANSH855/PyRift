import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy065_pkgutil_find_loader import PkgutilFindLoaderRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY065:
    rule = PkgutilFindLoaderRule()

    def test_detects_find_loader_import(self):
        findings = run(self.rule, "from pkgutil import find_loader")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY065"
        assert findings[0].severity == Severity.ERROR

    def test_detects_get_loader_import(self):
        findings = run(self.rule, "from pkgutil import get_loader")
        assert len(findings) == 1

    def test_detects_find_loader_call(self):
        findings = run(self.rule, "import pkgutil\npkgutil.find_loader('mod')")
        assert len(findings) == 1

    def test_clean_importlib_find_spec(self):
        findings = run(self.rule, "import importlib\nimportlib.util.find_spec('mod')")
        assert len(findings) == 0

    def test_suggestion_mentions_find_spec(self):
        findings = run(self.rule, "from pkgutil import find_loader")
        assert "find_spec" in findings[0].suggestion
