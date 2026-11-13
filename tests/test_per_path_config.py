"""Tests for [[tool.pyrift.per-path]] per-directory configuration overrides."""
from __future__ import annotations

import pytest

from pyrift.targets import PerPathConfig, _read_per_path

# ---------------------------------------------------------------------------
# Unit tests for PerPathConfig.matches
# ---------------------------------------------------------------------------


def test_matches_exact_filename():
    cfg = PerPathConfig(path="tests/foo.py")
    assert cfg.matches("tests/foo.py")


def test_matches_glob_star():
    cfg = PerPathConfig(path="tests/*.py")
    assert cfg.matches("tests/foo.py")
    assert not cfg.matches("src/foo.py")


def test_matches_glob_double_star():
    cfg = PerPathConfig(path="tests/**")
    assert cfg.matches("tests/cpython/test_cpy033.py")


def test_matches_subpath():
    cfg = PerPathConfig(path="tests/**")
    assert cfg.matches("project/tests/foo.py")


def test_no_match():
    cfg = PerPathConfig(path="tests/**")
    assert not cfg.matches("src/main.py")


# ---------------------------------------------------------------------------
# Unit tests for _read_per_path
# ---------------------------------------------------------------------------


def test_read_per_path_empty():
    assert _read_per_path([]) == ()


def test_read_per_path_none():
    assert _read_per_path(None) == ()


def test_read_per_path_single_ignore():
    result = _read_per_path([{"path": "tests/**", "ignore": ["CPY001"]}])
    assert len(result) == 1
    assert result[0].path == "tests/**"
    assert result[0].ignore == ("CPY001",)
    assert result[0].select is None


def test_read_per_path_single_select():
    result = _read_per_path([{"path": "src/**", "select": ["CPY033", "CPY034"]}])
    assert result[0].select == ("CPY033", "CPY034")
    assert result[0].ignore is None


def test_read_per_path_multiple():
    result = _read_per_path([
        {"path": "tests/**", "ignore": ["CPY001"]},
        {"path": "legacy/**", "select": ["CPY033"]},
    ])
    assert len(result) == 2
    assert result[0].path == "tests/**"
    assert result[1].path == "legacy/**"


def test_read_per_path_both_raises():
    with pytest.raises(ValueError, match="cannot set both"):
        _read_per_path([{"path": "tests/**", "select": ["CPY001"], "ignore": ["CPY002"]}])


def test_read_per_path_missing_path_raises():
    with pytest.raises(ValueError, match="'path'"):
        _read_per_path([{"ignore": ["CPY001"]}])


# ---------------------------------------------------------------------------
# Integration test: scan() respects per-path overrides
# ---------------------------------------------------------------------------


def test_scan_per_path_ignore(tmp_path):
    """Files matching per-path ignore pattern must not produce those findings."""
    from pyrift.scanner import scan

    # CPY002 fires on e.add_note(...)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("e.add_note('x')\n")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_foo.py").write_text("e.add_note('x')\n")

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example"\n\n'
        "[[tool.pyrift.per-path]]\n"
        'path = "tests/**"\n'
        'ignore = ["CPY002"]\n'
    )

    from pyrift.targets import load_pyrift_config, PerPathConfig
    _cfg = load_pyrift_config(tmp_path)
    assert _cfg is not None, f"load_pyrift_config returned None for {tmp_path}"
    assert len(_cfg.per_path) == 1, f"expected 1 per-path entry, got {_cfg.per_path}"
    _pc = _cfg.per_path[0]
    assert _pc.matches(str(tests_dir / "test_foo.py")), (
        f"matches() returned False for {tests_dir / 'test_foo.py'!r} against {_pc.path!r}"
    )

    result = scan(tmp_path)

    src_findings = [f for f in result.findings if "src" in f.file and f.rule_id == "CPY002"]
    test_findings = [f for f in result.findings if "tests" in f.file and f.rule_id == "CPY002"]

    assert len(src_findings) >= 1, "CPY002 must fire in src/"
    assert len(test_findings) == 0, "CPY002 must be suppressed in tests/"


def test_scan_per_path_select(tmp_path):
    """Files matching per-path select must only produce those rule findings."""
    from pyrift.scanner import scan

    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    # CPY007 fires on `import cgi` (removed module), CPY002 fires on add_note
    (legacy_dir / "old.py").write_text("import cgi\ne.add_note('x')\n")

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example"\n\n'
        "[[tool.pyrift.per-path]]\n"
        'path = "legacy/**"\n'
        'select = ["CPY007"]\n'
    )

    from pyrift.targets import load_pyrift_config
    _cfg = load_pyrift_config(tmp_path)
    assert _cfg is not None, f"load_pyrift_config returned None for {tmp_path}"
    assert len(_cfg.per_path) == 1, f"expected 1 per-path entry, got {_cfg.per_path}"
    _pc = _cfg.per_path[0]
    assert _pc.matches(str(legacy_dir / "old.py")), (
        f"matches() returned False for {legacy_dir / 'old.py'!r} against {_pc.path!r}"
    )

    result = scan(tmp_path)

    legacy_findings = [f for f in result.findings if "legacy" in f.file]
    legacy_rule_ids = {f.rule_id for f in legacy_findings}

    assert "CPY007" in legacy_rule_ids, "CPY007 must fire in legacy/"
    assert "CPY002" not in legacy_rule_ids, "CPY002 must be excluded in legacy/"