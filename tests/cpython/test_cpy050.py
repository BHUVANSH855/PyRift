import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy050_purepatth_is_reserved import PurePathIsReservedRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY050:
    rule = PurePathIsReservedRule()

    def test_detects_is_reserved(self):
        findings = run(self.rule,
            "from pathlib import PurePath\np = PurePath('CON')\np.is_reserved()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY050"
        assert findings[0].severity == Severity.WARNING

    def test_clean_other_pathlib_method(self):
        findings = run(self.rule, "p.is_absolute()")
        assert len(findings) == 0

    def test_suggestion_mentions_os_path(self):
        findings = run(self.rule, "p.is_reserved()")
        assert "os.path.isreserved" in findings[0].suggestion