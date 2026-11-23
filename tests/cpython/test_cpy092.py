"""Tests for CPY092 -- logging.warn() removed 3.13."""
from __future__ import annotations

import ast

from pyrift.rules.cpython.cpy092_logging_warn import LoggingWarnRule

RULE = LoggingWarnRule()


def _findings(src: str):
    return RULE.check(ast.parse(src), "test.py")


# --- True positives ---

def test_logging_warn():
    src = "import logging\nlogging.warn('msg')\n"
    f = _findings(src)
    assert any(r.rule_id == "CPY092" for r in f)


def test_logger_warn():
    src = (
        "import logging\n"
        "logger = logging.getLogger(__name__)\n"
        "logger.warn('msg')\n"
    )
    f = _findings(src)
    assert any(r.rule_id == "CPY092" for r in f)


def test_root_logger_warn():
    src = "import logging\nlog = logging.getLogger()\nlog.warn('oops')\n"
    f = _findings(src)
    assert any(r.rule_id == "CPY092" for r in f)


def test_warn_with_format_args():
    src = "import logging\nlogging.warn('error: %s', exc)\n"
    f = _findings(src)
    assert any(r.rule_id == "CPY092" for r in f)


# --- True negatives ---

def test_logging_warning_ok():
    src = "import logging\nlogging.warning('msg')\n"
    # Should NOT be flagged
    findings = _findings(src)
    # Only warn is flagged, not warning
    for f in findings:
        assert "logging.warn" not in f.description or "warning" in f.suggestion


def test_logging_error_ok():
    src = "import logging\nlogging.error('err')\n"
    assert _findings(src) == []


def test_logging_info_ok():
    src = "import logging\nlogging.info('info')\n"
    assert _findings(src) == []


def test_empty_file():
    assert _findings("") == []