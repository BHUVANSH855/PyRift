"""
pyrift.targets
~~~~~~~~~~~~~~
Project Python-version target detection and compatibility filtering.
"""
from __future__ import annotations

import importlib
import re
import types
from dataclasses import dataclass
from pathlib import Path

try:
    tomllib: types.ModuleType | None = importlib.import_module("tomllib")
except ModuleNotFoundError:
    tomllib = None

from .finding import Finding, Runtime

_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?$")

_REQUIRES_PYTHON_RE = re.compile(
    r'^\s*requires-python\s*=\s*["\']([^"\']+)["\']\s*$'
)


@dataclass(frozen=True)
class PythonVersion:
    """A Python major/minor version."""

    major: int
    minor: int

    @classmethod
    def parse(cls, value: str) -> PythonVersion:
        value = value.strip()

        match = _VERSION_RE.fullmatch(value)
        if not match:
            raise ValueError(f"Unsupported Python version: {value!r}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2) or 0),
        )

    def __lt__(self, other: PythonVersion) -> bool:
        return (self.major, self.minor) < (other.major, other.minor)

    def __le__(self, other: PythonVersion) -> bool:
        return (self.major, self.minor) <= (other.major, other.minor)

    def __gt__(self, other: PythonVersion) -> bool:
        return (self.major, self.minor) > (other.major, other.minor)

    def __ge__(self, other: PythonVersion) -> bool:
        return (self.major, self.minor) >= (other.major, other.minor)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass(frozen=True)
class TargetConfig:
    """
    Python versions, runtime, and platform supported by the project.

    ``None`` means the corresponding side of the version range is unbounded,
    no target runtime was specified, or no target platform was specified.
    """

    minimum: PythonVersion | None = None
    maximum: PythonVersion | None = None
    runtime: Runtime | None = None
    platform: str | None = None

    def affects_cpython(self, finding: Finding) -> bool:
        """
        Return True when a CPython finding intersects the project's
        supported Python-version range.
        """
        if finding.runtime not in (Runtime.CPYTHON, Runtime.BOTH):
            return False

        finding_min = (
            PythonVersion.parse(finding.affected_from)
            if finding.affected_from
            else None
        )

        finding_max = (
            PythonVersion.parse(finding.affected_until)
            if finding.affected_until
            else None
        )

        if (
            self.maximum is not None
            and finding_min is not None
            and finding_min > self.maximum
        ):
            return False

        return not (
            self.minimum is not None
            and finding_max is not None
            and finding_max < self.minimum
        )

    def allows_runtime(self, runtime: Runtime) -> bool:
        """
        Return True when ``runtime`` is allowed by this target.

        A ``None`` runtime target preserves the historical behavior and allows
        every runtime. A target of ``both`` also allows every runtime. A
        specific target allows that runtime and cross-runtime rules.
        """
        if self.runtime is None or self.runtime is Runtime.BOTH:
            return True

        return runtime in (self.runtime, Runtime.BOTH)


def _parse_version_specifier(specifier: str) -> TargetConfig:
    """
    Parse the intentionally small subset of PEP 440 specifiers that
    pyrift needs for Python-version targeting.

    Supported forms:

        >=3.10
        >3.10
        <=3.13
        <3.14
        ==3.12
        >=3.10,<3.14
        >=3.10,<=3.13

    Unsupported specifiers raise ValueError rather than silently
    producing an incorrect compatibility range.
    """
    minimum: PythonVersion | None = None
    maximum: PythonVersion | None = None

    for raw_part in specifier.split(","):
        part = raw_part.strip()

        if not part:
            continue

        if part.startswith(">="):
            version = PythonVersion.parse(part[2:])

            if minimum is None or version > minimum:
                minimum = version

            continue

        if part.startswith(">"):
            version = PythonVersion.parse(part[1:])

            # A strict lower bound such as >3.11 means the first
            # supported Python release is the next minor version.
            candidate = PythonVersion(
                version.major,
                version.minor + 1,
            )

            if minimum is None or candidate > minimum:
                minimum = candidate

            continue

        if part.startswith("<="):
            version = PythonVersion.parse(part[2:])

            if maximum is None or version < maximum:
                maximum = version

            continue

        if part.startswith("<"):
            version = PythonVersion.parse(part[1:])

            if version.minor > 0:
                candidate = PythonVersion(
                    version.major,
                    version.minor - 1,
                )
            else:
                candidate = PythonVersion(
                    version.major - 1,
                    11,
                )

            if maximum is None or candidate < maximum:
                maximum = candidate

            continue

        if part.startswith("=="):
            version = PythonVersion.parse(part[2:])

            if minimum is None or version > minimum:
                minimum = version

            if maximum is None or version < maximum:
                maximum = version

            continue

        raise ValueError(
            f"Unsupported Python version specifier: {part!r}"
        )

    if (
        minimum is not None
        and maximum is not None
        and minimum > maximum
    ):
        raise ValueError(
            f"Invalid Python version range: {specifier!r}"
        )

    return TargetConfig(
        minimum=minimum,
        maximum=maximum,
    )


def _load_requires_python_without_tomllib(
    pyproject: Path,
) -> str | None:
    """
    Extract project.requires-python for Python versions without tomllib.

    This is intentionally not a general TOML parser. It only supports
    the standard pyproject.toml layout needed by pyrift:

        [project]
        requires-python = ">=3.10,<3.14"

    If the structure is ambiguous or unsupported, return None rather
    than guessing.
    """
    try:
        lines = pyproject.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    in_project_table = False

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            in_project_table = stripped == "[project]"
            continue

        if not in_project_table:
            continue

        match = _REQUIRES_PYTHON_RE.match(stripped)

        if match:
            return match.group(1)

    return None


def load_project_targets(project_path: str | Path) -> TargetConfig | None:
    """
    Read ``project.requires-python`` from the ``pyproject.toml``
    associated with ``project_path``.

    When tomllib is available, use the standard-library TOML parser.

    On Python versions before 3.11, use the intentionally limited
    fallback parser for the simple [project] /
    requires-python form.

    Returns None when:
    - no pyproject.toml exists;
    - the file has no [project] table;
    - requires-python is not declared;
    - the TOML is invalid;
    - the version specifier is unsupported.
    """
    path = Path(project_path)

    if path.is_file():
        directory = path.parent
    else:
        directory = path

    # Resolve the nearest project configuration by walking upward. This makes
    # ``pyrift scan src/package`` behave the same as ``pyrift scan .`` when
    # the project's pyproject.toml lives at the repository root.
    directory = directory.resolve()
    for candidate_directory in (directory, *directory.parents):
        pyproject = candidate_directory / "pyproject.toml"
        if pyproject.exists():
            break
    else:
        return None

    requires_python: str | None = None

    if tomllib is not None:
        try:
            with pyproject.open("rb") as file:
                data = tomllib.load(file)
        except (OSError, tomllib.TOMLDecodeError):
            return None

        project = data.get("project")

        if not isinstance(project, dict):
            return None

        value = project.get("requires-python")

        if not isinstance(value, str):
            return None

        requires_python = value
    else:
        requires_python = _load_requires_python_without_tomllib(
            pyproject
        )

    if requires_python is None:
        return None

    try:
        return _parse_version_specifier(requires_python)
    except ValueError:
        return None