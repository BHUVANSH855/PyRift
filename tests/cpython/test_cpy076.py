"""Tests for CPY076 — ssl.wrap_socket() deprecated 3.7, removed 3.12."""
import ast
import textwrap

from pyrift.finding import Severity
from pyrift.rules.cpython.cpy076_ssl_wrap_socket import SslWrapSocketRule


def parse(src): return ast.parse(textwrap.dedent(src))
def run(rule, src): return rule.check(parse(src), "<test>")


class TestCPY076:
    rule = SslWrapSocketRule()

    # ------------------------------------------------------------------ #
    # Detection                                                            #
    # ------------------------------------------------------------------ #

    def test_detects_from_import(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY076"
        assert findings[0].severity == Severity.ERROR

    def test_from_import_col_offset_is_alias_level(self):
        # "from ssl import wrap_socket"
        # col 0         col 16
        src = "from ssl import wrap_socket"
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].col == src.index("wrap_socket")

    def test_detects_attribute_access_call(self):
        findings = run(self.rule, "import ssl\nssl.wrap_socket(sock)")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY076"

    def test_attribute_access_line_number(self):
        src = textwrap.dedent("""\
            import ssl
            ssl.wrap_socket(sock)
        """)
        findings = run(self.rule, src)
        assert len(findings) == 1
        assert findings[0].line == 2

    def test_detects_attribute_access_with_kwargs(self):
        src = "import ssl\nssl.wrap_socket(sock, server_side=True)"
        findings = run(self.rule, src)
        assert len(findings) == 1

    # ------------------------------------------------------------------ #
    # Negative cases                                                       #
    # ------------------------------------------------------------------ #

    def test_clean_create_default_context(self):
        findings = run(self.rule, "import ssl\nssl.create_default_context()")
        assert len(findings) == 0

    def test_clean_sslcontext_wrap_socket(self):
        """ctx.wrap_socket() on an SSLContext instance must NOT fire."""
        src = textwrap.dedent("""\
            import ssl
            ctx = ssl.create_default_context()
            ctx.wrap_socket(sock, server_hostname="example.com")
        """)
        findings = run(self.rule, src)
        assert len(findings) == 0

    def test_clean_import_ssl_only(self):
        findings = run(self.rule, "import ssl")
        assert len(findings) == 0

    def test_clean_unrelated_from_ssl_import(self):
        findings = run(self.rule, "from ssl import SSLContext, PROTOCOL_TLS_SERVER")
        assert len(findings) == 0

    def test_clean_string_literal_not_flagged(self):
        findings = run(self.rule, 'fn = "wrap_socket"')
        assert len(findings) == 0

    def test_clean_other_module_wrap_socket(self):
        """wrap_socket from a different module must NOT fire."""
        findings = run(self.rule, "import myssl\nmyssl.wrap_socket(sock)")
        assert len(findings) == 0

    def test_clean_bare_name_call_not_flagged(self):
        """Bare wrap_socket() call without ssl. prefix is not flagged (by design)."""
        findings = run(self.rule, "wrap_socket(sock)")
        assert len(findings) == 0

    def test_clean_empty_file(self):
        findings = run(self.rule, "")
        assert len(findings) == 0

    # ------------------------------------------------------------------ #
    # Multi-import / deduplication                                         #
    # ------------------------------------------------------------------ #

    def test_multi_import_produces_one_finding_for_wrap_socket(self):
        # Only wrap_socket fires; create_default_context is clean
        src = "from ssl import wrap_socket, create_default_context"
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_import_then_call_one_finding(self):
        """from-import fires; bare Name call does NOT fire (by design)."""
        src = textwrap.dedent("""\
            from ssl import wrap_socket
            wrap_socket(sock)
        """)
        findings = run(self.rule, src)
        assert len(findings) == 1

    def test_two_attribute_access_calls_two_findings(self):
        src = textwrap.dedent("""\
            import ssl
            ssl.wrap_socket(a)
            ssl.wrap_socket(b)
        """)
        findings = run(self.rule, src)
        assert len(findings) == 2

    # ------------------------------------------------------------------ #
    # Suggestion / description / metadata                                  #
    # ------------------------------------------------------------------ #

    def test_suggestion_mentions_sslcontext(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert "SSLContext" in findings[0].suggestion or "ctx.wrap_socket" in findings[0].suggestion

    def test_suggestion_mentions_create_default_context(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert "create_default_context" in findings[0].suggestion

    def test_description_mentions_deprecated_version(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert "3.7" in findings[0].description

    def test_description_mentions_removal_version(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert "3.12" in findings[0].description

    def test_severity_is_error(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert findings[0].severity == Severity.ERROR

    def test_affected_from_is_3_7(self):
        """Deprecated in 3.7; detection starts there, not at removal (3.12)."""
        findings = run(self.rule, "from ssl import wrap_socket")
        assert findings[0].affected_from == "3.7"

    def test_affected_until_is_empty(self):
        """Removal rule — fires forever from 3.7 onward."""
        findings = run(self.rule, "from ssl import wrap_socket")
        assert not findings[0].affected_until

    def test_docs_url_has_ssl_anchor(self):
        findings = run(self.rule, "from ssl import wrap_socket")
        assert findings[0].docs_url.endswith("#ssl")