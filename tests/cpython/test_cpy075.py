"""Tests for CPY075 — http.server.CGIHTTPRequestHandler deprecated 3.13, removed 3.15."""
import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy075_http_server_cgi import HttpServerCGIHandlerRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")


class TestCPY075:
    rule = HttpServerCGIHandlerRule()

    # ------------------------------------------------------------------ #
    # from-import detection                                                #
    # ------------------------------------------------------------------ #

    def test_detects_from_import(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY075"
        assert findings[0].severity == Severity.ERROR

    def test_from_import_col_offset_is_alias_level(self):
        # The alias for CGIHTTPRequestHandler starts at col 24 in
        # "from http.server import CGIHTTPRequestHandler"
        src = "from http.server import CGIHTTPRequestHandler"
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].col == src.index("CGIHTTPRequestHandler")

    def test_detects_bare_name_node(self):
        findings = run(self.rule, "CGIHTTPRequestHandler()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY075"

    def test_detects_attribute_access(self):
        findings = run(self.rule, "import http.server; http.server.CGIHTTPRequestHandler()")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY075"

    # ------------------------------------------------------------------ #
    # Negative cases                                                       #
    # ------------------------------------------------------------------ #

    def test_clean_simple_http_handler_import(self):
        findings = run(self.rule, "from http.server import SimpleHTTPRequestHandler")
        assert len(findings) == 0

    def test_clean_http_server_import(self):
        findings = run(self.rule, "import http.server")
        assert len(findings) == 0

    def test_clean_unrelated_attribute(self):
        findings = run(self.rule, "http.server.BaseHTTPRequestHandler()")
        assert len(findings) == 0

    def test_clean_unrelated_name(self):
        findings = run(self.rule, "BaseHTTPRequestHandler()")
        assert len(findings) == 0

    def test_clean_string_literal_not_flagged(self):
        # A string containing the class name must NOT fire.
        findings = run(self.rule, 'handler = "CGIHTTPRequestHandler"')
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # ------------------------------------------------------------------ #
    # Deduplication                                                        #
    # ------------------------------------------------------------------ #

    def test_no_duplicate_when_import_and_name_on_same_line(self):
        # The import statement introduces a Name node in the alias;
        # a separate usage on a different line should produce exactly 2 findings.
        src = textwrap.dedent("""\
            from http.server import CGIHTTPRequestHandler
            CGIHTTPRequestHandler()
        """)
        findings = run(self.rule, src)
        # import alias is on line 1, bare Name is on line 2 → 2 distinct positions
        assert len(findings) == 2

    # ------------------------------------------------------------------ #
    # Suggestion / description correctness                                 #
    # ------------------------------------------------------------------ #

    def test_suggestion_does_not_claim_simple_is_direct_replacement(self):
        # Official docs: "No direct replacement exists."
        # The suggestion may MENTION SimpleHTTPRequestHandler as a fallback
        # for static serving, but must NOT imply it replaces CGI functionality.
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        suggestion = findings[0].suggestion
        assert "no direct replacement" in suggestion.lower()

    def test_suggestion_recommends_wsgi_or_asgi(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        suggestion = findings[0].suggestion.lower()
        assert any(kw in suggestion for kw in ("wsgi", "asgi", "flask", "fastapi", "gunicorn", "uwsgi"))

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert "3.13" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert "3.15" in findings[0].description

    # ------------------------------------------------------------------ #
    # Metadata                                                             #
    # ------------------------------------------------------------------ #

    def test_affected_from_is_3_13(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert findings[0].affected_from == "3.13"

    def test_affected_until_is_empty(self):
        """Removed in 3.15 — no upper bound (fires forever from 3.13 onward)."""
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert findings[0].affected_until == ""

    def test_docs_url_points_to_3_15_removed(self):
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert "3.15" in findings[0].docs_url
        assert "removed" in findings[0].docs_url

    def test_severity_is_error(self):
        """Removed in 3.15 — severity is ERROR."""
        findings = run(self.rule, "from http.server import CGIHTTPRequestHandler")
        assert findings[0].severity == Severity.ERROR