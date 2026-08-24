import ast, textwrap
from pyrift.finding import Severity
from pyrift.rules.cpython.cpy030_sys_path_bytes import SysPathBytesRule

def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY030:
    rule = SysPathBytesRule()

    def test_detects_bytes_in_sys_path_append(self):
        findings = run(self.rule,
            "import sys\nsys.path.append(b'/some/path')")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY030"
        assert findings[0].severity == Severity.ERROR

    def test_detects_bytes_in_sys_path_insert(self):
        findings = run(self.rule,
            "import sys\nsys.path.insert(0, b'/path')")
        assert len(findings) == 1

    def test_clean_string_path(self):
        findings = run(self.rule,
            "import sys\nsys.path.append('/some/path')")
        assert len(findings) == 0

    def test_suggestion_mentions_str(self):
        findings = run(self.rule, "sys.path.append(b'/path')")
        assert "str" in findings[0].suggestion.lower()