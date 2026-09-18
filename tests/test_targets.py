from pathlib import Path

import pytest

from pyrift.finding import Finding, Runtime
from pyrift.targets import (
    PythonVersion,
    TargetConfig,
    load_project_targets,
)


def test_python_version_parsing():
    assert PythonVersion.parse("3.12") == PythonVersion(3, 12)


def test_python_version_comparison_le_and_ge():
    older = PythonVersion(3, 10)
    newer = PythonVersion(3, 12)

    assert older <= newer
    assert newer >= older
    assert older <= PythonVersion(3, 10)
    assert newer >= PythonVersion(3, 12)


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


def test_less_than_major_only_leaves_maximum_unbounded_in_fallback(
    monkeypatch,
):
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    config = targets._parse_version_specifier_fallback("<4")

    assert config.minimum is None
    assert config.maximum is None


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


def test_packaging_specifier_with_no_supported_versions_raises(monkeypatch):
    from pyrift import targets

    class FakeSpecifierSet:
        def __init__(self, specifier):
            self.specifier = specifier

        def contains(self, version, prereleases=True):
            return False

    class FakeVersion:
        def __init__(self, value):
            self.value = value

    monkeypatch.setattr(targets, "_SpecifierSet", FakeSpecifierSet)
    monkeypatch.setattr(targets, "_PkgVersion", FakeVersion)

    with pytest.raises(ValueError, match="matches no supported version"):
        targets._parse_version_specifier_packaging(">=99")


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


def test_affects_cpython_ignores_pypy_finding():
    config = TargetConfig(
        minimum=PythonVersion(3, 10),
        maximum=PythonVersion(3, 13),
    )

    finding = Finding(
        file="x.py",
        line=1,
        runtime=Runtime.PYPY,
        affected_from="3.10",
    )

    assert not config.affects_cpython(finding)


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


def test_parse_version_specifier_fallback_common_forms(monkeypatch):
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    cases = [
        (">=3.10", "3.10", None),
        (">3.10", "3.11", None),
        ("<=3.13", None, "3.13"),
        ("<3.14", None, "3.13"),
        ("==3.12", "3.12", "3.12"),
        ("~=3.11", "3.11", None),
        (">=3.10,<3.14", "3.10", "3.13"),
        (">=3.10,<=3.13", "3.10", "3.13"),
        (">=3.10.0", "3.10", None),
        ("!=3.11.0", None, None),
    ]

    for specifier, minimum, maximum in cases:
        result = targets._parse_version_specifier(specifier)

        if minimum is None:
            assert result.minimum is None
        else:
            assert str(result.minimum) == minimum

        if maximum is None:
            assert result.maximum is None
        else:
            assert str(result.maximum) == maximum


def test_parse_version_specifier_fallback_invalid_range():
    from pyrift import targets

    with pytest.raises(ValueError):
        targets._parse_version_specifier_fallback(">=3.14,<3.10")


def test_parse_version_specifier_fallback_unsupported():
    from pyrift import targets

    with pytest.raises(ValueError):
        targets._parse_version_specifier_fallback("===3.12")


def test_parse_version_specifier_fallback_empty_parts():
    from pyrift import targets

    result = targets._parse_version_specifier_fallback(
        ">=3.10,,<3.14"
    )

    assert result.minimum == targets.PythonVersion(3, 10)
    assert result.maximum == targets.PythonVersion(3, 13)


def test_parse_major_minor_with_patch():
    from pyrift.targets import PythonVersion, _parse_major_minor

    assert _parse_major_minor("3.12.4") == PythonVersion(3, 12)
    assert _parse_major_minor("3.11") == PythonVersion(3, 11)


def test_requires_python_without_tomllib(tmp_path):
    from pyrift.targets import _load_requires_python_without_tomllib

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'requires-python = ">=3.10,<3.14"\n',
        encoding="utf-8",
    )

    assert (
        _load_requires_python_without_tomllib(pyproject)
        == ">=3.10,<3.14"
    )


def test_requires_python_without_tomllib_missing(tmp_path):
    from pyrift.targets import _load_requires_python_without_tomllib

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "example"\n',
        encoding="utf-8",
    )

    assert _load_requires_python_without_tomllib(pyproject) is None


def test_pyrift_config_without_tomllib(tmp_path, monkeypatch):
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        'select = ["CPY038", "CPY067"]\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_pyrift_config(tmp_path)

    assert config is not None
    assert config.select == ("CPY038", "CPY067")
    assert config.ignore is None


def test_pyrift_config_ignore_without_tomllib(tmp_path, monkeypatch):
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        'ignore = ["PPY014", "PPY027"]\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_pyrift_config(tmp_path)

    assert config is not None
    assert config.select is None
    assert config.ignore == ("PPY014", "PPY027")


def test_pyrift_config_without_tomllib_invalid_value(
    tmp_path,
    monkeypatch,
):
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        'select = "CPY038"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    with pytest.raises(ValueError):
        targets.load_pyrift_config(tmp_path)


def test_pyrift_config_without_tomllib_non_string(
    tmp_path,
    monkeypatch,
):
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        "select = [1, 2]\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    with pytest.raises(ValueError):
        targets.load_pyrift_config(tmp_path)


def test_pyrift_config_without_tomllib_both_select_ignore(
    tmp_path,
    monkeypatch,
):
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        'select = ["CPY038"]\n'
        'ignore = ["PPY014"]\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    with pytest.raises(ValueError):
        targets.load_pyrift_config(tmp_path)


def test_pyrift_config_without_tomllib_malformed_array(
    tmp_path,
    monkeypatch,
):
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        "select = [CPY038]\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    with pytest.raises(ValueError):
        targets.load_pyrift_config(tmp_path)


def test_parse_version_specifier_fallback_accepts_empty_part(
    monkeypatch,
) -> None:
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    result = targets._parse_version_specifier(">=3.12,")

    assert result.minimum == targets.PythonVersion(3, 12)
    assert result.maximum is None


def test_parse_version_specifier_fallback_rejects_invalid_operator(
    monkeypatch,
) -> None:
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    with pytest.raises(
        ValueError,
        match="Unsupported Python version specifier",
    ):
        targets._parse_version_specifier("=>3.12")


def test_parse_version_specifier_fallback_handles_multiple_specifiers(
    monkeypatch,
) -> None:
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    result = targets._parse_version_specifier(
        ">=3.10,<3.14"
    )

    assert result.minimum is not None
    assert str(result.minimum) == "3.10"
    assert result.maximum is not None
    assert str(result.maximum) == "3.13"


def test_parse_major_minor_rejects_missing_version() -> None:
    from pyrift import targets

    with pytest.raises(ValueError):
        targets._parse_major_minor("")


def test_requires_python_fallback_ignores_other_project_keys(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "example"
version = "1.0"

[build-system]
requires = ["setuptools"]

requires-python = ">=3.11"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    result = targets._load_requires_python_without_tomllib(
        pyproject
    )

    assert result is None


def test_pyrift_config_fallback_ignores_other_tables(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "example"

[tool.other]
select = ["CPY001"]

[tool.pyrift]
select = ["CPY038"]
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    result = targets.load_pyrift_config(tmp_path)

    assert result is not None
    assert result.select == ("CPY038",)
    assert result.ignore is None


def test_pyrift_config_fallback_ignores_comments(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
# Project configuration

[tool.pyrift]
# Select compatibility rules
select = ["CPY038"]
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    result = targets.load_pyrift_config(tmp_path)

    assert result is not None
    assert result.select == ("CPY038",)


def test_pyrift_config_fallback_rejects_unquoted_values(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift]
select = [CPY038]
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    with pytest.raises(
        ValueError,
        match="must be an array of strings",
    ):
        targets.load_pyrift_config(tmp_path)


def test_pyrift_config_fallback_rejects_non_array(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift]
select = "CPY038"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    with pytest.raises(
        ValueError,
        match="must be an array of strings",
    ):
        targets.load_pyrift_config(tmp_path)


def test_load_project_targets_without_pyproject(tmp_path) -> None:
    assert load_project_targets(tmp_path) is None


def test_load_project_targets_with_invalid_toml(
    tmp_path,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project
name = "broken"
""",
        encoding="utf-8",
    )

    result = targets.load_project_targets(tmp_path)

    assert result is None


def test_load_pyrift_config_with_invalid_toml(
    tmp_path,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift
select = ["CPY038"]
""",
        encoding="utf-8",
    )

    result = targets.load_pyrift_config(tmp_path)

    assert result is None

def test_parse_version_specifier_fallback_empty_specifier(
    monkeypatch,
) -> None:
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    result = targets._parse_version_specifier("")

    assert result.minimum is None
    assert result.maximum is None


def test_parse_version_specifier_fallback_invalid_version(
    monkeypatch,
) -> None:
    from pyrift import targets

    monkeypatch.setattr(targets, "_HAS_PACKAGING", False)

    with pytest.raises(ValueError):
        targets._parse_version_specifier(">=invalid")


def test_python_version_parse_rejects_invalid_input() -> None:
    with pytest.raises(ValueError):
        PythonVersion.parse("invalid")


def test_python_version_parse_accepts_major_only() -> None:
    assert PythonVersion.parse("3") == PythonVersion(3, 0)


def test_finding_without_affected_from_matches_unbounded_finding() -> None:
    config = TargetConfig(
        minimum=PythonVersion(3, 10),
        maximum=PythonVersion(3, 13),
    )

    finding = Finding(
        file="x.py",
        line=1,
        runtime=Runtime.CPYTHON,
    )

    assert config.affects_cpython(finding)


def test_requires_python_fallback_ignores_non_project_lines(
    tmp_path,
) -> None:
    from pyrift.targets import _load_requires_python_without_tomllib

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
name = "example"

[build-system]
requires = ["setuptools"]

[project]
name = "example"
requires-python = ">=3.11"
""",
        encoding="utf-8",
    )

    assert (
        _load_requires_python_without_tomllib(pyproject)
        == ">=3.11"
    )


def test_requires_python_fallback_ignores_invalid_project_assignment(
    tmp_path,
) -> None:
    from pyrift.targets import _load_requires_python_without_tomllib

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "example"
requires-python
""",
        encoding="utf-8",
    )

    assert _load_requires_python_without_tomllib(pyproject) is None


def test_requires_python_fallback_handles_comment_lines(
    tmp_path,
) -> None:
    from pyrift.targets import _load_requires_python_without_tomllib

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
# comment
[project]
# another comment
requires-python = ">=3.11"
""",
        encoding="utf-8",
    )

    assert (
        _load_requires_python_without_tomllib(pyproject)
        == ">=3.11"
    )


def test_pyrift_config_fallback_ignores_unknown_keys(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift]
unknown = ["CPY001"]
select = ["CPY038"]
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_pyrift_config(tmp_path)

    assert config is not None
    assert config.select == ("CPY038",)


def test_pyrift_config_fallback_ignores_invalid_lines(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift]
this is not an assignment
select = ["CPY038"]
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_pyrift_config(tmp_path)

    assert config is not None
    assert config.select == ("CPY038",)


def test_pyrift_config_fallback_empty_select(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift]
select = []
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_pyrift_config(tmp_path)

    assert config is not None
    assert config.select == ()
    assert config.ignore is None


def test_pyrift_config_fallback_empty_ignore(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.pyrift]
ignore = []
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_pyrift_config(tmp_path)

    assert config is not None
    assert config.select is None
    assert config.ignore == ()


def test_pyrift_config_fallback_unknown_table(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.other]
select = ["CPY001"]
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    assert targets.load_pyrift_config(tmp_path) is None


# ---------------------------------------------------------------------------
# Additional coverage for targets.py
# ---------------------------------------------------------------------------


def test_requires_python_fallback_returns_none_on_read_error(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'requires-python = ">=3.10"\n',
        encoding="utf-8",
    )

    def raise_os_error(self, encoding=None):
        raise OSError("read failed")

    monkeypatch.setattr(Path, "read_text", raise_os_error)

    assert targets._load_requires_python_without_tomllib(pyproject) is None


def test_pyrift_config_fallback_returns_none_on_read_error(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.pyrift]\n"
        'select = ["CPY038"]\n',
        encoding="utf-8",
    )

    def raise_os_error(self, encoding=None):
        raise OSError("read failed")

    monkeypatch.setattr(Path, "read_text", raise_os_error)

    assert targets._load_pyrift_config_without_tomllib(
        pyproject
    ) == (None, None)


def test_load_project_targets_accepts_pyproject_file_path(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'requires-python = ">=3.10,<3.14"\n',
        encoding="utf-8",
    )

    config = load_project_targets(pyproject)

    assert config is not None
    assert config.minimum == PythonVersion(3, 10)
    assert config.maximum == PythonVersion(3, 13)


def test_project_table_with_non_mapping_value_returns_none(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        'project = "not-a-table"\n',
        encoding="utf-8",
    )

    assert load_project_targets(tmp_path) is None


def test_load_pyrift_config_with_non_mapping_table_returns_none(tmp_path):
    from pyrift import targets

    (tmp_path / "pyproject.toml").write_text(
        'tool.pyrift = "not-a-table"\n',
        encoding="utf-8",
    )

    assert targets.load_pyrift_config(tmp_path) is None

def test_load_project_targets_without_requires_python_fallback_returns_none(
    tmp_path,
    monkeypatch,
) -> None:
    from pyrift import targets

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        'name = "example"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(targets, "tomllib", None)

    assert targets.load_project_targets(tmp_path) is None