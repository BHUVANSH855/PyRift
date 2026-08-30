import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy075_http_server_cgi import HttpServerCGIHandlerRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")

class TestCPY075:
    rule = HttpServerCGIHandlerRule()

    def test_detects_import(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY075"
        assert findings[0].severity == Severity.WARNING

    def test_detects_usage(self):
        findings = run(self.rule, "CGIHTTPRequestHandler()")
        assert len(findings) >= 1

    def test_clean_simple_http_handler(self):
        findings = run(self.rule, "from http.server import SimpleHTTPRequestHandler")
        assert len(findings) == 0

    def test_suggestion_mentions_simple(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert "SimpleHTTPRequestHandler" in findings[0].suggestion
