import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy028_lib2to3 import Lib2to3Rule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY028:
    rule = Lib2to3Rule()

    def test_detects_lib2to3_import(self):
        findings = run(self.rule, "import lib2to3")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY028"
        assert findings[0].severity == Severity.ERROR

    def test_detects_lib2to3_submodule(self):
        findings = run(self.rule, "from lib2to3.pygram import python_grammar")
        assert len(findings) == 1

    def test_clean_other_import(self):
        findings = run(self.rule, "import ast")
        assert len(findings) == 0

    def test_suggestion_mentions_libcst(self):
        findings = run(self.rule, "import lib2to3")
        assert "libcst" in findings[0].suggestion.lower()