"""Tests for CPY087 -- ssl deprecated protocol constants."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy087_ssl_deprecated_protocols import (
    SslDeprecatedProtocolsRule,
)

RULE = SslDeprecatedProtocolsRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_ssl_protocol_tls():
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    f = _findings(src)
    assert len(f) == 1
    assert f[0].rule_id == "CPY087"


def test_ssl_protocol_tlsv1():
    src = "import ssl\nssl.PROTOCOL_TLSv1\n"
    assert len(_findings(src)) == 1


def test_ssl_protocol_tlsv1_1():
    src = "import ssl\nssl.PROTOCOL_TLSv1_1\n"
    assert len(_findings(src)) == 1


def test_ssl_protocol_sslv23():
    src = "import ssl\nssl.PROTOCOL_SSLv23\n"
    assert len(_findings(src)) == 1


def test_ssl_op_no_sslv2():
    src = "import ssl\nssl.OP_NO_SSLv2\n"
    assert len(_findings(src)) == 1


def test_ssl_op_no_tlsv1():
    src = "import ssl\nssl.OP_NO_TLSv1\n"
    assert len(_findings(src)) == 1


def test_ssl_protocol_tlsv1_2_flagged():
    # PROTOCOL_TLSv1_2 is in the deprecated set (deprecated 3.6)
    src = "import ssl\nssl.PROTOCOL_TLSv1_2\n"
    assert len(_findings(src)) == 1


def test_multiple_deprecated():
    src = (
        "import ssl\n"
        "ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)\n"
        "ctx.options |= ssl.OP_NO_TLSv1_1\n"
    )
    assert len(_findings(src)) == 2


# --- True negatives ---

def test_ssl_create_default_context():
    src = "import ssl\nssl.create_default_context()\n"
    assert _findings(src) == []


def test_ssl_sslcontext_ok():
    src = "import ssl\nssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)\n"
    assert _findings(src) == []


def test_unrelated_ssl_attr():
    src = "import ssl\nssl.CERT_REQUIRED\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []


# --- Metadata assertions ---

def test_affected_from_is_3_10():
    # Runtime DeprecationWarning added in 3.10 (bpo-43880 / gh-25455)
    # Docs-only deprecation started earlier (3.6/3.7) but PyRift tracks
    # the runtime warning behaviour, so affected_from is 3.10.
    src = "import ssl\nssl.PROTOCOL_TLSv1\n"
    f = _findings(src)
    assert f[0].affected_from == "3.10", (
        f"Runtime DeprecationWarning from 3.10 (bpo-43880); got {f[0].affected_from!r}"
    )


def test_affected_until_is_empty():
    # Pending removal in future — no scheduled removal version
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    f = _findings(src)
    assert not f[0].affected_until


def test_severity_is_warning():
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    f = _findings(src)
    from pyrift.finding import Severity
    assert f[0].severity == Severity.WARNING


def test_description_names_deprecated_constant():
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    f = _findings(src)
    assert "PROTOCOL_TLS" in f[0].description


def test_suggestion_mentions_tls_client():
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    f = _findings(src)
    assert "PROTOCOL_TLS_CLIENT" in f[0].suggestion


def test_suggestion_mentions_minimum_version():
    src = "import ssl\nssl.OP_NO_TLSv1\n"
    f = _findings(src)
    assert "minimum_version" in f[0].suggestion


def test_docs_url_points_to_ssl():
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    f = _findings(src)
    assert "ssl" in f[0].docs_url
    assert "python.org" in f[0].docs_url


def test_rule_id_is_cpy087():
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    assert _findings(src)[0].rule_id == "CPY087"


def test_affected_until_is_exactly_empty_string():
    # Pending removal in future versions — no specific version scheduled
    src = "import ssl\nssl.PROTOCOL_TLS\n"
    assert _findings(src)[0].affected_until == "", (
        "No removal date; expected affected_until==''"
    )


# --- Remaining constants in deprecated set ---

def test_ssl_op_no_sslv3():
    src = "import ssl\nssl.OP_NO_SSLv3\n"
    assert len(_findings(src)) == 1


def test_ssl_op_no_tlsv1_1():
    src = "import ssl\nssl.OP_NO_TLSv1_1\n"
    assert len(_findings(src)) == 1


# --- Constant used in function call arg ---

def test_deprecated_constant_as_sslcontext_arg():
    src = "import ssl\nssl.SSLContext(ssl.PROTOCOL_TLSv1_2)\n"
    f = _findings(src)
    assert len(f) == 1
    assert "PROTOCOL_TLSv1_2" in f[0].description


def test_deprecated_constant_in_options_or():
    src = "import ssl\nctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)\nctx.options |= ssl.OP_NO_SSLv2\n"
    f = _findings(src)
    assert len(f) == 1
    assert "OP_NO_SSLv2" in f[0].description


# --- Multiple findings ---

def test_three_deprecated_constants_three_findings():
    src = (
        "import ssl\n"
        "ssl.PROTOCOL_TLS\n"
        "ssl.PROTOCOL_TLSv1\n"
        "ssl.OP_NO_TLSv1\n"
    )
    assert len(_findings(src)) == 3


def test_all_findings_are_warning_severity():
    from pyrift.finding import Severity
    src = (
        "import ssl\n"
        "ssl.PROTOCOL_SSLv23\n"
        "ssl.OP_NO_SSLv3\n"
    )
    findings = _findings(src)
    assert len(findings) == 2
    assert all(fi.severity == Severity.WARNING for fi in findings)


# --- Non-ssl attribute with same name not flagged ---

def test_non_ssl_object_not_flagged():
    # Only ssl.PROTOCOL_TLS* should fire, not myobj.PROTOCOL_TLS
    src = "myobj.PROTOCOL_TLS\n"
    assert _findings(src) == []


def test_ssl_protocol_tls_client_not_flagged():
    # PROTOCOL_TLS_CLIENT is the recommended replacement — must NOT be flagged
    src = "import ssl\nssl.PROTOCOL_TLS_CLIENT\n"
    assert _findings(src) == []


def test_ssl_protocol_tls_server_not_flagged():
    src = "import ssl\nssl.PROTOCOL_TLS_SERVER\n"
    assert _findings(src) == []