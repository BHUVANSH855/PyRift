import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy064_ast_deprecated_nodes import AstDeprecatedNodesRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY064:
    rule = AstDeprecatedNodesRule()

    def test_detects_ast_num(self):
        findings = run(self.rule, "import ast\nisinstance(x, ast.Num)")
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY064"
        assert findings[0].severity == Severity.ERROR

    def test_detects_ast_str(self):
        findings = run(self.rule, "isinstance(x, ast.Str)")
        assert len(findings) >= 1
        assert findings[0].rule_id == "CPY064"

    def test_detects_ast_bytes(self):
        findings = run(self.rule, "ast.Bytes")
        assert len(findings) >= 1

    def test_detects_ast_nameconstant(self):
        findings = run(self.rule, "ast.NameConstant")
        assert len(findings) >= 1

    def test_detects_ast_ellipsis(self):
        findings = run(self.rule, "ast.Ellipsis")
        assert len(findings) >= 1

    def test_clean_ast_constant(self):
        findings = run(self.rule, "import ast\nast.Constant")
        assert len(findings) == 0

    def test_clean_ast_name(self):
        findings = run(self.rule, "import ast\nast.Name")
        assert len(findings) == 0

    def test_suggestion_mentions_constant(self):
        findings = run(self.rule, "ast.Num")
        assert "ast.Constant" in findings[0].suggestion
