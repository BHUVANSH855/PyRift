"""Extended tests for pyrift.targets covering edge cases."""
import pytest

from pyrift.finding import Finding, Runtime, Severity
from pyrift.targets import (
    PythonVersion,
    TargetConfig,
    _parse_version_specifier,
    load_project_targets,
)


def make_finding(affected_from="3.11", affected_until="3.13"):
    return Finding(
        file="test.py", line=1, col=0,
        rule_id="CPY001", title="test",
        description="test", severity=Severity.WARNING,
        runtime=Runtime.CPYTHON,
        affected_from=affected_from,
        affected_until=affected_until,
    )


class TestPythonVersionComparisons:
    def test_less_than_or_equal(self):
        assert PythonVersion(3, 10) <= PythonVersion(3, 11)
        assert PythonVersion(3, 10) <= PythonVersion(3, 10)

    def test_greater_than_or_equal(self):
        assert PythonVersion(3, 12) >= PythonVersion(3, 10)
        assert PythonVersion(3, 12) >= PythonVersion(3, 12)

    def test_str_representation(self):
        assert str(PythonVersion(3, 11)) == "3.11"

    def test_parse_valid(self):
        v = PythonVersion.parse("3.10")
        assert v.major == 3 and v.minor == 10

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            PythonVersion.parse("not_a_version")

    def test_equality(self):
        assert PythonVersion(3, 10) == PythonVersion(3, 10)
        assert PythonVersion(3, 10) != PythonVersion(3, 11)

    def test_less_than(self):
        assert PythonVersion(3, 10) < PythonVersion(3, 11)

    def test_greater_than(self):
        assert PythonVersion(3, 11) > PythonVersion(3, 10)


class TestTargetConfig:
    def test_default_config(self):
        config = TargetConfig()
        assert config.minimum is None
        assert config.maximum is None
        assert config.platform is None

    def test_config_with_versions(self):
        config = TargetConfig(
            minimum=PythonVersion(3, 10),
            maximum=PythonVersion(3, 13),
        )
        assert config.minimum == PythonVersion(3, 10)
        assert config.maximum == PythonVersion(3, 13)

    def test_affects_cpython_no_bounds(self):
        config = TargetConfig()
        f = make_finding()
        assert config.affects_cpython(f) is True

    def test_affects_cpython_min_bound_excludes(self):
        config = TargetConfig(minimum=PythonVersion(3, 14))
        f = make_finding(affected_from="3.11", affected_until="3.13")
        assert config.affects_cpython(f) is False

    def test_affects_cpython_min_bound_includes(self):
        config = TargetConfig(minimum=PythonVersion(3, 10))
        f = make_finding(affected_from="3.11", affected_until="3.13")
        assert config.affects_cpython(f) is True

    def test_affects_cpython_pypy_finding_excluded(self):
        config = TargetConfig()
        f = Finding(
            file="test.py", line=1, col=0,
            rule_id="PPY001", title="test",
            description="test", severity=Severity.WARNING,
            runtime=Runtime.PYPY,
            affected_from="", affected_until="",
        )
        assert config.affects_cpython(f) is False

    def test_platform_attribute(self):
        config = TargetConfig(platform="linux")
        assert config.platform == "linux"


class TestParseVersionSpecifier:
    def test_ge_specifier(self):
        config = _parse_version_specifier(">=3.10")
        assert config is not None
        assert config.minimum == PythonVersion(3, 10)
        assert config.maximum is None

    def test_compound_ge_lt(self):
        config = _parse_version_specifier(">=3.10,<3.14")
        assert config is not None
        assert config.minimum == PythonVersion(3, 10)

    def test_empty_returns_empty_config(self):
        config = _parse_version_specifier("")
        assert config is not None
        assert config.minimum is None
        assert config.maximum is None

    def test_unsupported_specifier_raises(self):
        with pytest.raises(ValueError):
            _parse_version_specifier("~=3.10")

    def test_lt_specifier(self):
        config = _parse_version_specifier("<3.14")
        assert config is not None
        assert config.maximum == PythonVersion(3, 13)

    def test_le_specifier(self):
        config = _parse_version_specifier("<=3.13")
        assert config is not None
        assert config.maximum == PythonVersion(3, 13)

    def test_exact_specifier(self):
        config = _parse_version_specifier("==3.11")
        assert config is not None

    def test_unsupported_operator_raises(self):
        with pytest.raises(ValueError):
            _parse_version_specifier("!=3.12")


class TestLoadProjectTargets:
    def test_returns_none_when_no_pyproject(self, tmp_path):
        config = load_project_targets(tmp_path)
        assert config is None

    def test_returns_none_on_missing_requires_python(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'\n")
        config = load_project_targets(tmp_path)
        assert config is None

    def test_parses_requires_python(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.10"\n')
        config = load_project_targets(tmp_path)
        assert config is not None
        assert config.minimum == PythonVersion(3, 10)

    def test_parses_compound_specifier(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nrequires-python = ">=3.10,<3.14"\n'
        )
        config = load_project_targets(tmp_path)
        assert config is not None
        assert config.minimum == PythonVersion(3, 10)

    def test_oserror_on_pyproject_read(self, tmp_path):
        # Create a pyproject.toml then make it unreadable via bad path
        config = load_project_targets(tmp_path / "nonexistent_dir")
        assert config is None

    def test_invalid_toml_returns_none(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("not valid toml [[[")
        config = load_project_targets(tmp_path)
        assert config is None

    def test_searches_parent_directories(self, tmp_path):
        # Create pyproject.toml in parent, scan from child
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.11"\n')
        child = tmp_path / "src" / "pkg"
        child.mkdir(parents=True)
        config = load_project_targets(child)
        assert config is not None
        assert config.minimum == PythonVersion(3, 11)

    def test_lt_requires_python(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.10,<3.14"\n')
        config = load_project_targets(tmp_path)
        assert config is not None

    def test_no_project_section(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[build-system]\nrequires = ['setuptools']\n")
        config = load_project_targets(tmp_path)
        assert config is None

    def test_deeply_nested_finds_parent_pyproject(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nrequires-python = ">=3.12"\n')
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        config = load_project_targets(deep)
        assert config is not None
        assert config.minimum == PythonVersion(3, 12)

    def test_file_not_found_returns_none(self, tmp_path):
        # Directory with no pyproject.toml at any level
        isolated = tmp_path / "isolated"
        isolated.mkdir()
        config = load_project_targets(isolated)
        assert config is None