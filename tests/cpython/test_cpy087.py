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


def test_ssl_tlsv1_2_ok():
    src = "import ssl\nssl.PROTOCOL_TLSv1_2\n"
    # PROTOCOL_TLSv1_2 is in the deprecated set too
    assert len(_findings(src)) == 1


def test_ssl_sslcontext_ok():
    src = "import ssl\nssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)\n"
    assert _findings(src) == []


def test_unrelated_ssl_attr():
    src = "import ssl\nssl.CERT_REQUIRED\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []