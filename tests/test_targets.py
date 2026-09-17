import pytest

from pyrift.finding import Finding, Runtime
from pyrift.targets import (
    PythonVersion,
    TargetConfig,
    load_project_targets,
)


def test_python_version_parsing():
    assert PythonVersion.parse("3.12") == PythonVersion(3, 12)


def test_greater_than_or_equal_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 10)
    assert config.maximum is None


def test_bounded_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10,<3.14"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 10)
    assert config.maximum == PythonVersion(3, 13)


def test_greater_than_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">3.10"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 11)
    assert config.maximum is None


def test_greater_than_311_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">3.11"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 12)
    assert config.maximum is None


def test_less_than_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "<3.14"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum is None
    assert config.maximum == PythonVersion(3, 13)


def test_less_than_310_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "<3.10"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum is None
    assert config.maximum == PythonVersion(3, 9)


def test_exact_version_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "==3.12"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 12)
    assert config.maximum == PythonVersion(3, 12)


def test_missing_pyproject_returns_none(tmp_path):
    assert load_project_targets(tmp_path) is None


def test_missing_requires_python_returns_none(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'name = "example"\n'
    )

    assert load_project_targets(tmp_path) is None


def test_unsupported_specifier_returns_none(tmp_path):
    # `~=3.10` used to be unsupported (the exact PEP 440 gap flagged by
    # the 2026-09 audit); it's now parsed correctly (see
    # test_compatible_release_specifier below), so this test exercises a
    # genuinely malformed specifier instead.
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "not-a-valid-specifier"\n'
    )

    assert load_project_targets(tmp_path) is None


def test_compatible_release_specifier(tmp_path):
    """`~=3.11` (PEP 440 compatible-release) means >=3.11, ==3.*."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "~=3.11"\n'
    )

    config = load_project_targets(tmp_path)
    assert config is not None
    assert config.minimum == PythonVersion(3, 11)


def test_exclusion_clause_specifier(tmp_path):
    """`!=` exclusion clauses are accepted (not fatal) even though a
    single excluded minor can't be represented in a min/max range."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10,!=3.11.0,<3.15"\n'
    )

    config = load_project_targets(tmp_path)
    assert config is not None
    assert config.minimum == PythonVersion(3, 10)


def test_patch_version_specifier(tmp_path):
    """A patch-level bound like `>=3.10.4` is accepted, not rejected.

    Because ``PythonVersion`` only models major.minor granularity, a
    patch floor above ``.0`` conservatively excludes the whole minor it
    falls within (3.10.0 doesn't satisfy ``>=3.10.4``, so the earliest
    fully-satisfying minor is 3.11) rather than guessing which patches
    within 3.10 would qualify.
    """
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10.4,<3.15"\n'
    )

    config = load_project_targets(tmp_path)
    assert config is not None
    assert config.minimum == PythonVersion(3, 11)
    assert config.maximum == PythonVersion(3, 14)


def test_finding_intersects_supported_range():
    config = TargetConfig(
        minimum=PythonVersion(3, 10),
        maximum=PythonVersion(3, 13),
    )

    future = Finding(
        file="x.py",
        line=1,
        runtime=Runtime.CPYTHON,
        affected_from="3.14",
    )

    old = Finding(
        file="x.py",
        line=1,
        runtime=Runtime.CPYTHON,
        affected_from="3.0",
        affected_until="3.9",
    )

    relevant = Finding(
        file="x.py",
        line=1,
        runtime=Runtime.CPYTHON,
        affected_from="3.12",
    )

    assert not config.affects_cpython(future)
    assert not config.affects_cpython(old)
    assert config.affects_cpython(relevant)


def test_load_requires_python_without_tomllib(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10,<3.14"\n'
    )

    from pyrift import targets

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 10)
    assert config.maximum == PythonVersion(3, 13)


def test_load_project_targets_walks_to_parent(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.10,<3.14"\n'
    )

    nested = tmp_path / "src" / "package"
    nested.mkdir(parents=True)

    config = load_project_targets(nested)

    assert config is not None
    assert config.minimum == PythonVersion(3, 10)
    assert config.maximum == PythonVersion(3, 13)


def test_target_config_platform():
    config = TargetConfig(platform="windows")

    assert config.platform == "windows"


def test_target_config_platform_defaults_to_none():
    config = TargetConfig()

    assert config.platform is None


def test_target_config_runtime_defaults_to_none():
    config = TargetConfig()

    assert config.runtime is None


def test_target_config_runtime_roundtrip():
    config = TargetConfig(runtime=Runtime.CPYTHON)

    assert config.runtime is Runtime.CPYTHON


def test_target_config_allows_cpython():
    config = TargetConfig(runtime=Runtime.CPYTHON)

    assert config.allows_runtime(Runtime.CPYTHON)
    assert config.allows_runtime(Runtime.BOTH)
    assert not config.allows_runtime(Runtime.PYPY)


def test_target_config_allows_pypy():
    config = TargetConfig(runtime=Runtime.PYPY)

    assert config.allows_runtime(Runtime.PYPY)
    assert config.allows_runtime(Runtime.BOTH)
    assert not config.allows_runtime(Runtime.CPYTHON)


def test_target_config_allows_both():
    config = TargetConfig(runtime=Runtime.BOTH)

    assert config.allows_runtime(Runtime.CPYTHON)
    assert config.allows_runtime(Runtime.PYPY)
    assert config.allows_runtime(Runtime.BOTH)

class TestLoadPyriftConfig:
    """2026-09 audit item #34: [tool.pyrift] config-file support."""

    def test_returns_none_with_no_pyproject(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        assert load_pyrift_config(tmp_path) is None

    def test_returns_none_with_no_tool_pyrift_table(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\n'
        )
        assert load_pyrift_config(tmp_path) is None

    def test_reads_select_list(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "example"\n\n'
            "[tool.pyrift]\n"
            'select = ["CPY038", "CPY067"]\n'
        )
        config = load_pyrift_config(tmp_path)
        assert config is not None
        assert config.select == ("CPY038", "CPY067")
        assert config.ignore is None

    def test_reads_ignore_list(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pyrift]\n"
            'ignore = ["PPY014"]\n'
        )
        config = load_pyrift_config(tmp_path)
        assert config is not None
        assert config.ignore == ("PPY014",)
        assert config.select is None

    def test_both_select_and_ignore_raises(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pyrift]\n"
            'select = ["CPY038"]\n'
            'ignore = ["PPY014"]\n'
        )
        with pytest.raises(ValueError):
            load_pyrift_config(tmp_path)

    def test_non_list_select_raises(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pyrift]\n"
            'select = "CPY038"\n'
        )
        with pytest.raises(ValueError):
            load_pyrift_config(tmp_path)

    def test_non_string_list_entries_raises(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pyrift]\n"
            "select = [1, 2]\n"
        )
        with pytest.raises(ValueError):
            load_pyrift_config(tmp_path)

    def test_empty_tool_pyrift_table_returns_none(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pyrift]\n"
        )
        assert load_pyrift_config(tmp_path) is None

    def test_walks_up_to_find_pyproject_like_project_targets(self, tmp_path):
        from pyrift.targets import load_pyrift_config
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pyrift]\n"
            'select = ["CPY038"]\n'
        )
        nested = tmp_path / "src" / "package"
        nested.mkdir(parents=True)
        config = load_pyrift_config(nested)
        assert config is not None
        assert config.select == ("CPY038",)
