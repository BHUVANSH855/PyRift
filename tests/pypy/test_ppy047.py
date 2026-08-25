import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.pypy.ppy047_ctypes_find_library import CtypesFindLibraryRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestPPY047:
    rule = CtypesFindLibraryRule()

    def test_detects_find_library(self):
        findings = run(self.rule,
            "from ctypes.util import find_library\nfind_library('ssl')")
        assert len(findings) == 1
        assert findings[0].rule_id == "PPY047"
        assert findings[0].severity == Severity.WARNING

    def test_detects_ctypes_util_find_library(self):
        findings = run(self.rule,
            "import ctypes.util\nctypes.util.find_library('z')")
        assert len(findings) == 1

    def test_clean_other_ctypes_call(self):
        findings = run(self.rule,
            "import ctypes\nctypes.CDLL('libssl.so')")
        assert len(findings) == 0

    def test_suggestion_mentions_cffi(self):
        findings = run(self.rule, "find_library('ssl')")
        assert "cffi" in findings[0].suggestion.lower()