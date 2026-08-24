import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy035_c_extensions import CExtensionsRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY035:
    rule = CExtensionsRule()

    def test_detects_numpy(self):
        findings = run(self.rule, "import numpy")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY035"
        assert findings[0].severity == Severity.WARNING

    def test_detects_pandas(self):
        findings = run(self.rule, "import pandas as pd")
        assert len(findings) == 1

    def test_detects_from_import(self):
        findings = run(self.rule, "from scipy import stats")
        assert len(findings) == 1

    def test_clean_pure_python_package(self):
        findings = run(self.rule, "import requests")
        assert len(findings) == 0

    def test_suggestion_mentions_cffi(self):
        findings = run(self.rule, "import numpy")
        assert "cffi" in findings[0].suggestion.lower()