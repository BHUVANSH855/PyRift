"""
pyrift.scanner
~~~~~~~~~~~~~~
Core scanning engine.
Parses Python files into ASTs and runs all registered rules.
"""
from __future__ import annotations

import ast
import os
from collections.abc import Iterator
from pathlib import Path

from .base_rule import BaseRule
from .finding import Finding, Runtime
from .targets import TargetConfig, load_project_targets
from .rules.cpython.cpy001_dict_ordering import DictOrderingRule
from .rules.cpython.cpy002_exception_notes import ExceptionNotesRule
from .rules.cpython.cpy003_union_type_syntax import UnionTypeSyntaxRule
from .rules.cpython.cpy004_tomllib import TomllibRule
from .rules.cpython.cpy005_match_case import MatchCaseRule
from .rules.cpython.cpy006_asyncio_timeout import AsyncioTimeoutRule
from .rules.cpython.cpy007_removed_modules import RemovedModulesRule
from .rules.cpython.cpy008_slots_dict import SlotsDictRule
from .rules.cpython.cpy009_exception_group import ExceptionGroupRule
from .rules.cpython.cpy010_dataclass_slots import DataclassSlotsRule
from .rules.cpython.cpy011_typing_self import TypingSelfRule
from .rules.cpython.cpy012_literal_string import LiteralStringRule
from .rules.cpython.cpy013_override import OverrideRule
from .rules.cpython.cpy014_type_alias import TypeAliasRule
from .rules.cpython.cpy015_never import NeverRule
from .rules.cpython.cpy016_typevartuple import TypeVarTupleRule
from .rules.cpython.cpy017_unpack import UnpackRule
from .rules.cpython.cpy018_required import RequiredRule
from .rules.cpython.cpy019_distutils import DistutilsRule
from .rules.cpython.cpy020_datetime_utc import DatetimeUTCRule
from .rules.cpython.cpy021_asyncio_coroutine import AsyncioIsCoroutineRule
from .rules.cpython.cpy022_bool_inversion import BoolInversionRule
from .rules.cpython.cpy023_multiprocessing_fork import MultiprocessingForkRule
from .rules.cpython.cpy024_typeguard import TypeGuardRule
from .rules.cpython.cpy025_paramspec import ParamSpecRule
from .rules.cpython.cpy026_typing_io_re import TypingIoReRule
from .rules.cpython.cpy027_locale_resetlocale import LocaleResetlocaleRule
from .rules.cpython.cpy028_lib2to3 import Lib2to3Rule
from .rules.cpython.cpy029_locals_behaviour import LocalsBehaviourRule
from .rules.cpython.cpy030_sys_path_bytes import SysPathBytesRule
from .rules.cpython.cpy031_assert_never import AssertNeverRule
from .rules.cpython.cpy032_reveal_type import RevealTypeRule
from .rules.cpython.cpy033_is_relative_to import IsRelativeToRule
from .rules.cpython.cpy034_bit_count import BitCountRule
from .rules.cpython.cpy035_removeprefix import RemovePrefixRule
from .rules.cpython.cpy036_datetime_utcnow import DatetimeUtcnowRule
from .rules.cpython.cpy037_datetime_utcfromtimestamp import DatetimeUtcfromtimestampRule
from .rules.cpython.cpy038_asyncio_get_event_loop import AsyncioGetEventLoopRule
from .rules.cpython.cpy039_zoneinfo import ZoneInfoRule
from .rules.cpython.cpy040_graphlib import GraphlibRule
from .rules.cpython.cpy041_dict_merge_operator import DictMergeOperatorRule
from .rules.cpython.cpy042_aiter_anext import AiterAnextRule
from .rules.cpython.cpy043_math_lcm import MathLcmRule
from .rules.cpython.cpy044_math_gcd_multi import MathGcdMultiRule
from .rules.cpython.cpy045_nan_hash import NanHashRule
from .rules.pypy.ppy001_gc_finalizer import GcFinalizerRule
from .rules.pypy.ppy002_ctypes import CtypesRule
from .rules.pypy.ppy003_getrefcount import GetRefcountRule
from .rules.pypy.ppy004_weakref_proxy import WeakrefProxyRule
from .rules.pypy.ppy005_io_buffering import IoBufferingRule
from .rules.pypy.ppy006_builtin_monkey_patch import BuiltinMonkeyPatchRule
from .rules.pypy.ppy007_sys_intern import SysInternRule
from .rules.pypy.ppy008_threading_local import ThreadingLocalRule
from .rules.pypy.ppy009_id_stability import IdStabilityRule
from .rules.pypy.ppy010_gc_collect import GcCollectRule
from .rules.pypy.ppy011_array import ArrayTypeCodeRule
from .rules.pypy.ppy012_subclassing_builtins import SubclassingBuiltinsRule
from .rules.pypy.ppy013_getsizeof import GetSizeofRule
from .rules.pypy.ppy014_string_concat import StringConcatLoopRule
from .rules.pypy.ppy015_generator_gc import GeneratorGCRule
from .rules.pypy.ppy016_instance_dict_order import InstanceDictOrderRule
from .rules.pypy.ppy017_del_existing_class import DelExistingClassRule
from .rules.pypy.ppy018_recursion_limit import RecursionLimitRule
from .rules.pypy.ppy019_nan_identity import NanIdentityRule
from .rules.pypy.ppy020_kwargs_string_keys import KwargsStringKeysRule
from .rules.pypy.ppy021_socket_gc import SocketGCRule
from .rules.pypy.ppy022_hash_randomisation import HashRandomisationRule
from .rules.pypy.ppy023_inspect_ismethod import InspectIsMethodRule
from .rules.pypy.ppy024_timeit import TimeitRule
from .rules.pypy.ppy025_set_ordering import SetOrderingRule
from .rules.pypy.ppy026_builtins_module import BuiltinsModuleRule
from .rules.pypy.ppy027_module_attr_delete import ModuleAttrDeleteRule
from .rules.pypy.ppy028_readline_parse_bind import ReadlineParseBindRule
from .rules.pypy.ppy029_dict_kwargs_nonstring import BuiltinsAssignRule
from .rules.pypy.ppy030_sys_flags import SysFlagsRule
from .rules.pypy.ppy031_integer_identity import IntegerIdentityRule
from .rules.pypy.ppy032_dict_key_mutation import DictKeyMutationRule
from .rules.pypy.ppy033_del_ignored_exceptions import DelIgnoredExceptionsRule
from .rules.pypy.ppy034_hash_minus_one import HashMinusOneRule
from .rules.pypy.ppy035_c_extensions import CExtensionsRule
from .rules.pypy.ppy036_open_flush import OpenFlushRule
from .rules.pypy.ppy037_os_urandom import OsUrandomRule
from .rules.pypy.ppy038_decimal import DecimalBackendRule
from .rules.pypy.ppy039_os_fork import OsForkRule
from .rules.pypy.ppy040_subprocess_pipe import SubprocessPipeRule
from .rules.pypy.ppy041_dict_merge_pypy import DictMergePypyRule
from .rules.pypy.ppy042_print_flush import PrintFlushRule
from .rules.pypy.ppy043_slots_memory import SlotsMemorypyRule
from .rules.pypy.ppy044_exception_chaining import ExceptionChainingRule
from .rules.pypy.ppy045_sys_settrace import SysSettraceRule

ALL_RULES: list[BaseRule] = [
    DictOrderingRule(),
    ExceptionNotesRule(),
    UnionTypeSyntaxRule(),
    TomllibRule(),
    MatchCaseRule(),
    AsyncioTimeoutRule(),
    RemovedModulesRule(),
    SlotsDictRule(),
    ExceptionGroupRule(),
    DataclassSlotsRule(),
    GcFinalizerRule(),
    CtypesRule(),
    GetRefcountRule(),
    WeakrefProxyRule(),
    IoBufferingRule(),
    BuiltinMonkeyPatchRule(),
    SysInternRule(),
    TypingSelfRule(),
    LiteralStringRule(),
    OverrideRule(),
    TypeAliasRule(),
    NeverRule(),
    TypeVarTupleRule(),
    UnpackRule(),
    RequiredRule(),
    ThreadingLocalRule(),
    IdStabilityRule(),
    GcCollectRule(),
    ArrayTypeCodeRule(),
    SubclassingBuiltinsRule(),
    DistutilsRule(),
    DatetimeUTCRule(),
    GetSizeofRule(),
    StringConcatLoopRule(),
    GeneratorGCRule(),
    InstanceDictOrderRule(),
    DelExistingClassRule(),
    RecursionLimitRule(),
    NanIdentityRule(),
    KwargsStringKeysRule(),
    AsyncioIsCoroutineRule(),
    BoolInversionRule(),
    MultiprocessingForkRule(),
    TypeGuardRule(),
    ParamSpecRule(),
    SocketGCRule(),
    HashRandomisationRule(),
    InspectIsMethodRule(),
    TimeitRule(),
    SetOrderingRule(),
    TypingIoReRule(),
    LocaleResetlocaleRule(),
    Lib2to3Rule(),
    LocalsBehaviourRule(),
    SysPathBytesRule(),
    BuiltinsModuleRule(),
    ModuleAttrDeleteRule(),
    ReadlineParseBindRule(),
    BuiltinsAssignRule(),
    SysFlagsRule(),
    AssertNeverRule(),
    RevealTypeRule(),
    IsRelativeToRule(),
    BitCountRule(),
    RemovePrefixRule(),
    IntegerIdentityRule(),
    DictKeyMutationRule(),
    DelIgnoredExceptionsRule(),
    HashMinusOneRule(),
    CExtensionsRule(),
    DatetimeUtcnowRule(),
    DatetimeUtcfromtimestampRule(),
    AsyncioGetEventLoopRule(),
    ZoneInfoRule(),
    GraphlibRule(),
    OpenFlushRule(),
    OsUrandomRule(),
    DecimalBackendRule(),
    OsForkRule(),
    SubprocessPipeRule(),
    DictMergeOperatorRule(),
    AiterAnextRule(),
    MathLcmRule(),
    MathGcdMultiRule(),
    NanHashRule(),
    DictMergePypyRule(),
    PrintFlushRule(),
    SlotsMemorypyRule(),
    ExceptionChainingRule(),
    SysSettraceRule(),
]

SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env",
    "node_modules", ".tox", "dist", "build", ".eggs",
}


class ScanResult:
    """Holds all findings from a scan run."""

    def __init__(
        self,
        findings: list[Finding],
        files_scanned: int,
        baseline_suppressed: int = 0,
    ):
        self.findings            = findings
        self.files_scanned       = files_scanned
        self.baseline_suppressed = baseline_suppressed

    @property
    def errors(self) -> list[Finding]:
        from .finding import Severity
        return [f for f in self.findings if f.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        from .finding import Severity
        return [f for f in self.findings if f.severity == Severity.WARNING]

    @property
    def score(self) -> int:
        deductions = len(self.errors) * 10 + len(self.warnings) * 3
        return max(0, 100 - deductions)

    def __repr__(self) -> str:
        base = (
            f"ScanResult(files={self.files_scanned}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)}, "
            f"score={self.score})"
        )
        if self.baseline_suppressed:
            base += f" [baseline suppressed: {self.baseline_suppressed}]"
        return base


def _python_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def scan_file(filepath: str | Path,
              rules: list[BaseRule] | None = None) -> list[Finding]:
    """Scan a single file. Returns list of Findings."""
    filepath = Path(filepath)
    rules = rules or ALL_RULES
    findings: list[Finding] = []

    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree   = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        from .finding import Runtime, Severity
        findings.append(Finding(
            file=str(filepath),
            line=exc.lineno or 0,
            rule_id="PARSE",
            title="Syntax error — file could not be parsed",
            description=str(exc),
            severity=Severity.ERROR,
            runtime=Runtime.BOTH,
        ))
        return findings

    for rule in rules:
        try:
            findings.extend(rule.check(tree, str(filepath)))
        except Exception:
            pass

    return findings


def scan(
    path: str | Path,
    rules: list[BaseRule] | None = None,
    target_config: TargetConfig | None = None,
    use_project_config: bool = True,
) -> ScanResult:
    """
    Scan a file or directory tree.

    When ``use_project_config`` is True, pyrift reads
    ``project.requires-python`` from ``pyproject.toml`` and removes
    CPython findings that cannot affect the project's supported
    Python versions.

    An explicitly supplied ``target_config`` takes precedence over
    project configuration.

    Usage::

        import pyrift

        result = pyrift.scan("./myproject")

        for finding in result.findings:
            print(finding)
    """
    path = Path(path)

    if target_config is None and use_project_config:
        target_config = load_project_targets(path)

    all_findings: list[Finding] = []
    files_scanned = 0

    for py_file in _python_files(path):
        findings = scan_file(py_file, rules)

        if target_config is not None:
            findings = [
                finding
                for finding in findings
                if (
                    finding.runtime not in (
                        Runtime.CPYTHON,
                        Runtime.BOTH,
                    )
                    or target_config.affects_cpython(finding)
                )
            ]

        all_findings.extend(findings)
        files_scanned += 1

    return ScanResult(all_findings, files_scanned)