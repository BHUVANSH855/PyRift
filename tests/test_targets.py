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


def test_less_than_range(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "<3.14"\n'
    )

    config = load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum is None
    assert config.maximum == PythonVersion(3, 13)


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
    (tmp_path / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = "~=3.10"\n'
    )

    assert load_project_targets(tmp_path) is None


def test_finding_intersects_supported_range():
    config = TargetConfig(
        minimum=PythonVersion(3, 10),
        maximum=PythonVersion(3, 13),
    )

    from pyrift.finding import Finding, Runtime

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

    import pyrift.targets as targets

    monkeypatch.setattr(targets, "tomllib", None)

    config = targets.load_project_targets(tmp_path)

    assert config is not None
    assert config.minimum == PythonVersion(3, 10)
    assert config.maximum == PythonVersion(3, 13)
