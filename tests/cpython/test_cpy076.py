import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy076_ssl_wrap_socket import SslWrapSocketRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY076:
    rule = SslWrapSocketRule()

    def test_detects_import(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY076"
        assert findings[0].severity == Severity.ERROR

    def test_detects_call(self):
        findings = run(self.rule, "import ssl\nssl.wrap_socket(sock)")
        assert len(findings) == 1

    def test_clean_create_default_context(self):
        findings = run(self.rule, "import ssl\nssl.create_default_context()")
        assert len(findings) == 0

    def test_suggestion_mentions_context(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert "SSLContext" in findings[0].suggestion or "wrap_socket" in findings[0].suggestion
