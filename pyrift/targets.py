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

# `packaging` is an optional soft-dependency (not required at install time --
# PyRift keeps a zero-hard-dependency default per the 2026-09 audit's
# packaging-risk discussion). When present, it gives PyRift a correct,
# complete PEP 440 parser (~=, !=, X.Y.Z patch versions, .* wildcards,
# multi-clause specifiers) instead of the small regex-based subset below.
# Add the `full` extra (``pip install pyrift[full]``) to get it.
try:
    from packaging.specifiers import SpecifierSet as _SpecifierSet
    from packaging.version import Version as _PkgVersion

    _HAS_PACKAGING = True
except ImportError:  # pragma: no cover - exercised via the fallback path
    _SpecifierSet = None  # type: ignore[misc,assignment]
    _PkgVersion = None  # type: ignore[misc,assignment]
    _HAS_PACKAGING = False

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
    Parse a ``requires-python`` style PEP 440 specifier into a
    ``TargetConfig``.

    When the optional ``packaging`` dependency is installed, this uses
    ``packaging.specifiers.SpecifierSet`` for a fully correct PEP 440
    parse (``~=``, ``!=``, ``X.Y.Z`` patch versions, ``.*`` wildcards,
    multi-clause specifiers such as ``>=3.10,!=3.11.0,<4``). Without it,
    :func:`_parse_version_specifier_fallback` handles the common subset
    real-world ``pyproject.toml`` files actually use.
    """
    if _HAS_PACKAGING:
        return _parse_version_specifier_packaging(specifier)
    return _parse_version_specifier_fallback(specifier)


def _parse_version_specifier_packaging(specifier: str) -> TargetConfig:
    try:
        spec_set = _SpecifierSet(specifier)
    except Exception as exc:  # packaging raises InvalidSpecifier
        raise ValueError(
            f"Unsupported Python version specifier: {specifier!r}"
        ) from exc

    # There is no closed-form inverse of an arbitrary PEP 440 specifier
    # set, so probe every (major, minor) pair in a generous supported
    # range and find the lowest/highest minor that satisfies the whole
    # specifier set at its `.0` patch release. This correctly handles
    # `~=`, `!=`, wildcards, and combinations of clauses without
    # re-implementing PEP 440 matching by hand.
    probe_majors = (2, 3, 4)
    probe_minors = range(40)

    candidates: list[PythonVersion] = []
    for major in probe_majors:
        for minor in probe_minors:
            probe = _PkgVersion(f"{major}.{minor}.0")
            if spec_set.contains(probe, prereleases=True):
                candidates.append(PythonVersion(major, minor))

    if not candidates:
        raise ValueError(
            f"Python version specifier matches no supported version: {specifier!r}"
        )

    lowest_probed = PythonVersion(probe_majors[0], probe_minors[0])
    highest_probed = PythonVersion(probe_majors[-1], probe_minors[-1])

    minimum: PythonVersion | None = min(candidates)
    maximum: PythonVersion | None = max(candidates)

    # If the match extends all the way to either edge of the probed
    # range, treat that side as genuinely unbounded (None) rather than
    # reporting the probe's arbitrary ceiling/floor as a real bound --
    # this matches the historical "None means unbounded" contract that
    # the rest of pyrift (TargetConfig.affects_cpython, CLI output, ...)
    # relies on.
    if minimum == lowest_probed:
        minimum = None
    if maximum == highest_probed:
        maximum = None

    return TargetConfig(minimum=minimum, maximum=maximum)


def _parse_version_specifier_fallback(specifier: str) -> TargetConfig:
    """
    Parse the subset of PEP 440 specifiers that ``pyrift`` supports
    without the optional ``packaging`` dependency.

    Supported forms:

        >=3.10
        >3.10
        <=3.13
        <3.14
        ==3.12
        ~=3.11
        >=3.10,<3.14
        >=3.10,<=3.13
        >=3.10.0            (patch component is accepted and ignored)
        !=3.11.0            (exclusion clauses are accepted and ignored --
                              they narrow the range but PyRift's
                              TargetConfig only tracks a min/max bound,
                              same as `Finding.parse_version_range`)

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
            version = _parse_major_minor(part[2:])

            if minimum is None or version > minimum:
                minimum = version

            continue

        if part.startswith(">"):
            version = _parse_major_minor(part[1:])

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
            version = _parse_major_minor(part[2:])

            if maximum is None or version < maximum:
                maximum = version

            continue

        if part.startswith("~="):
            # `~=3.11` means ">=3.11, ==3.*" (compatible release): the
            # major version is pinned, minor may be this value or higher.
            version = _parse_major_minor(part[2:])

            if minimum is None or version > minimum:
                minimum = version

            continue

        if part.startswith("!="):
            # Exclusion clause. TargetConfig only tracks a min/max range,
            # so a single excluded version can't be represented exactly;
            # accept and ignore it rather than failing the whole parse,
            # matching `Finding.parse_version_range`'s existing behavior.
            _parse_major_minor(part[2:].rstrip("*").rstrip("."))
            continue

        if part.startswith("<"):
            version = _parse_major_minor(part[1:])

            if version.minor > 0:
                upper_candidate: PythonVersion | None = PythonVersion(
                    version.major,
                    version.minor - 1,
                )
            else:
                # A bare "<X" with no minor component (e.g. "<4") means
                # "any version before major X" -- there's no principled
                # minor-level ceiling to infer for the previous major
                # from this clause alone (unlike a real PEP 440 parse,
                # which would just exclude major X entirely). Leave this
                # side unbounded; a companion `>=` clause on the same
                # major still constrains the effective range correctly.
                upper_candidate = None

            if upper_candidate is not None and (
                maximum is None or upper_candidate < maximum
            ):
                maximum = upper_candidate

            continue

        if part.startswith("=="):
            version = _parse_major_minor(part[2:].rstrip("*").rstrip("."))

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


def _parse_major_minor(value: str) -> PythonVersion:
    """Parse a version string, tolerating a patch component (``3.10.4``)
    by truncating it to major.minor, since ``PythonVersion`` only models
    major.minor granularity."""
    value = value.strip()
    parts = value.split(".")
    if len(parts) >= 2:
        value = f"{parts[0]}.{parts[1]}"
    return PythonVersion.parse(value)


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


def _load_pyrift_config_without_tomllib(
    pyproject: Path,
) -> tuple[list[str] | None, list[str] | None]:
    """
    Extract ``[tool.pyrift]`` select/ignore settings without tomllib.

    This intentionally supports only the simple configuration form used by
    PyRift:

        [tool.pyrift]
        select = ["CPY038", "CPY067"]

    or:

        [tool.pyrift]
        ignore = ["PPY014", "PPY027"]

    The fallback is deliberately conservative. If the table or values cannot
    be parsed unambiguously, raise ValueError rather than silently ignoring
    the user's configuration.
    """
    try:
        lines = pyproject.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None, None

    in_pyrift_table = False
    select: list[str] | None = None
    ignore: list[str] | None = None

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            in_pyrift_table = stripped == "[tool.pyrift]"
            continue

        if not in_pyrift_table:
            continue

        if "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if key not in {"select", "ignore"}:
            continue

        if not (
            raw_value.startswith("[")
            and raw_value.endswith("]")
        ):
            raise ValueError(
                "[tool.pyrift] 'select'/'ignore' must be an array of strings"
            )

        contents = raw_value[1:-1].strip()

        if not contents:
            values: list[str] = []
        else:
            values = []

            for item in contents.split(","):
                item = item.strip()

                if (
                    len(item) < 2
                    or item[0] != '"'
                    or item[-1] != '"'
                ):
                    raise ValueError(
                        "[tool.pyrift] 'select'/'ignore' must be an "
                        "array of strings"
                    )

                values.append(item[1:-1])

        if key == "select":
            select = values
        else:
            ignore = values

    return select, ignore


def _find_pyproject_toml(project_path: str | Path) -> Path | None:
    """Walk upward from *project_path* to find the nearest
    ``pyproject.toml``, the same discovery logic
    :func:`load_project_targets` uses, so ``pyrift scan src/package``
    finds the repository root's config the same way
    ``pyrift scan .`` does."""
    path = Path(project_path)

    if path.is_file():
        directory = path.parent
    else:
        directory = path

    directory = directory.resolve()
    for candidate_directory in (directory, *directory.parents):
        pyproject = candidate_directory / "pyproject.toml"
        if pyproject.exists():
            return pyproject

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
    pyproject = _find_pyproject_toml(project_path)

    if pyproject is None:
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


@dataclass(frozen=True)
class PyriftConfig:
    """
    Project-wide PyRift settings read from a ``[tool.pyrift]`` table in
    ``pyproject.toml``.

    Supported keys:

        [tool.pyrift]
        select = ["CPY038", "CPY067"]

    or:

        [tool.pyrift]
        ignore = ["PPY014", "PPY027"]

    ``select`` and ``ignore`` are mutually exclusive.
    """

    select: tuple[str, ...] | None = None
    ignore: tuple[str, ...] | None = None


def load_pyrift_config(project_path: str | Path) -> PyriftConfig | None:
    """
    Read the ``[tool.pyrift]`` table from ``pyproject.toml``.

    The nearest ``pyproject.toml`` is discovered by walking upward from
    ``project_path``.

    ``tomllib`` is preferred when available. On Python versions before
    3.11, the intentionally limited fallback parser handles the supported
    ``select``/``ignore`` configuration.

    Returns ``None`` when no PyRift configuration exists.

    Raises ``ValueError`` for malformed PyRift configuration.
    """
    pyproject = _find_pyproject_toml(project_path)

    if pyproject is None:
        return None

    if tomllib is not None:
        try:
            with pyproject.open("rb") as file:
                data = tomllib.load(file)
        except (OSError, tomllib.TOMLDecodeError):
            return None

        tool = data.get("tool")

        if not isinstance(tool, dict):
            return None

        pyrift_table = tool.get("pyrift")

        if not isinstance(pyrift_table, dict):
            return None

        select = _read_string_list(
            pyrift_table.get("select"),
            key="select",
        )
        ignore = _read_string_list(
            pyrift_table.get("ignore"),
            key="ignore",
        )
    else:
        select, ignore = _load_pyrift_config_without_tomllib(
            pyproject
        )

        if select is not None:
            select = tuple(select)

        if ignore is not None:
            ignore = tuple(ignore)

    if select is not None and ignore is not None:
        raise ValueError(
            "[tool.pyrift] cannot set both 'select' and 'ignore'"
        )

    if select is None and ignore is None:
        return None

    return PyriftConfig(
        select=select,
        ignore=ignore,
    )


def _read_string_list(
    value: object,
    *,
    key: str,
) -> tuple[str, ...] | None:
    """
    Validate a PyRift configuration list.

    ``None`` means the key was absent. Any present value must be a TOML
    array containing only strings.
    """
    if value is None:
        return None

    if not isinstance(value, list):
        raise TypeError(
            f"[tool.pyrift] '{key}' must be an array of strings"
        )

    if not all(isinstance(item, str) for item in value):
        raise TypeError(
            f"[tool.pyrift] '{key}' must be an array of strings"
        )

    return tuple(value)


def _read_string_list(value: object) -> tuple[str, ...] | None:
    """Validate that *value* is a TOML array of strings, returning it
    as a tuple, or None if the key was absent. Raises ValueError for
    anything malformed (wrong type, non-string entries) rather than
    silently ignoring a broken config."""
    if value is None:
        return None
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError(
            "[tool.pyrift] 'select'/'ignore' must be an array of strings"
        )
    return tuple(value)