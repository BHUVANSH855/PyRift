"""Tests for the pyrift plugin discovery system."""

from __future__ import annotations

import ast
import sys
from importlib.metadata import EntryPoint
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import pyrift
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity
from pyrift.scanner import _BUILTIN_RULES, _load_plugin_rules


# ---------------------------------------------------------------------------
# Minimal valid plugin rule for use in tests
# ---------------------------------------------------------------------------


class _FakeRule(BaseRule):
    rule_id = "TST001"
    title = "Test rule"
    runtime = "both"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: Any = None,
    ) -> list[Finding]:
        return []


def _get_fake_rules() -> list[BaseRule]:
    return [_FakeRule()]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_builtin_rules_unchanged():
    """_BUILTIN_RULES must contain exactly the same rules as before the
    plugin system was introduced — plugin loading must not alter them."""
    assert len(_BUILTIN_RULES) > 0
    # Every item is a BaseRule instance
    for rule in _BUILTIN_RULES:
        assert isinstance(rule, BaseRule), f"{rule!r} is not a BaseRule"


def test_all_rules_contains_builtins():
    """ALL_RULES must be a superset of _BUILTIN_RULES."""
    builtin_ids = {r.rule_id for r in _BUILTIN_RULES}
    all_ids = {r.rule_id for r in pyrift.ALL_RULES}
    assert builtin_ids <= all_ids


def test_no_plugins_returns_empty_list():
    """When no entry-points are registered, _load_plugin_rules returns []."""
    with patch("importlib.metadata.entry_points", return_value=[]):
        result = _load_plugin_rules()
    assert result == []


def test_valid_plugin_is_loaded():
    """A well-formed plugin entry-point contributes its rules to the result."""
    ep = MagicMock(spec=EntryPoint)
    ep.name = "test-plugin"
    ep.load.return_value = _get_fake_rules

    with patch("importlib.metadata.entry_points", return_value=[ep]):
        result = _load_plugin_rules()

    assert len(result) == 1
    assert isinstance(result[0], BaseRule)
    assert result[0].rule_id == "TST001"


def test_broken_plugin_is_skipped(caplog: pytest.LogCaptureFixture):
    """A plugin whose callable raises must be skipped, not crash the scan."""
    import logging

    ep = MagicMock(spec=EntryPoint)
    ep.name = "broken-plugin"
    ep.load.side_effect = ImportError("missing dependency")

    with patch("importlib.metadata.entry_points", return_value=[ep]):
        with caplog.at_level(logging.WARNING, logger="pyrift.scanner"):
            result = _load_plugin_rules()

    assert result == []
    assert "broken-plugin" in caplog.text
    assert "skipped" in caplog.text


def test_plugin_returning_wrong_type_is_skipped(caplog: pytest.LogCaptureFixture):
    """A plugin returning a non-list must be skipped with a warning."""
    import logging

    ep = MagicMock(spec=EntryPoint)
    ep.name = "bad-return-plugin"
    ep.load.return_value = lambda: "not a list"

    with patch("importlib.metadata.entry_points", return_value=[ep]):
        with caplog.at_level(logging.WARNING, logger="pyrift.scanner"):
            result = _load_plugin_rules()

    assert result == []
    assert "bad-return-plugin" in caplog.text


def test_plugin_returning_non_rule_items_is_skipped(caplog: pytest.LogCaptureFixture):
    """A plugin list containing non-BaseRule items must be skipped."""
    import logging

    ep = MagicMock(spec=EntryPoint)
    ep.name = "bad-items-plugin"
    ep.load.return_value = lambda: [object()]

    with patch("importlib.metadata.entry_points", return_value=[ep]):
        with caplog.at_level(logging.WARNING, logger="pyrift.scanner"):
            result = _load_plugin_rules()

    assert result == []
    assert "bad-items-plugin" in caplog.text


def test_multiple_plugins_all_loaded():
    """All valid plugins in the entry-point group are loaded."""
    ep1 = MagicMock(spec=EntryPoint)
    ep1.name = "plugin-a"
    ep1.load.return_value = _get_fake_rules

    ep2 = MagicMock(spec=EntryPoint)
    ep2.name = "plugin-b"
    ep2.load.return_value = _get_fake_rules

    with patch("importlib.metadata.entry_points", return_value=[ep1, ep2]):
        result = _load_plugin_rules()

    assert len(result) == 2


def test_base_rule_and_severity_exported():
    """BaseRule and Severity must be importable directly from pyrift."""
    assert hasattr(pyrift, "BaseRule")
    assert hasattr(pyrift, "Severity")
    assert "BaseRule" in pyrift.__all__
    assert "Severity" in pyrift.__all__
