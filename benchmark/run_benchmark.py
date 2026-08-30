#!/usr/bin/env python3
"""
pyrift golden benchmark runner.

Tests the reviewed golden cases and enforces the quality contracts
stored in benchmark/expected.json.

Usage:
    python benchmark/run_benchmark.py
    python benchmark/run_benchmark.py --verbose
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pyrift import ALL_RULES

RULES = {rule.rule_id: rule for rule in ALL_RULES}

EXPECTED_PATH = Path(__file__).parent / "expected.json"


def load_expected() -> dict[str, dict]:
    data = json.loads(
        EXPECTED_PATH.read_text(encoding="utf-8")
    )

    rules = data.get("rules")

    if not isinstance(rules, dict):
        raise TypeError(
            "benchmark/expected.json must contain a 'rules' object"
        )

    return rules


# Golden test cases:
# (source, should_flag, label)
GOLDEN = {
    "CPY001": [
        ("d.keys() == ['a', 'b']", True, "keys vs list"),
        ("set(d.keys()) == {'a', 'b'}", False, "set comparison safe"),
        ("d.keys() == other.keys()", False, "two key views"),
    ],
    "CPY002": [
        ("e.add_note('hint')", True, "add_note call"),
        ("e.args", False, "other attr"),
    ],
    "CPY003": [
        ("isinstance(x, int | str)", True, "union in isinstance"),
        ("x: int | str = 1", False, "annotation only"),
    ],
    "CPY004": [
        ("import tomllib", True, "tomllib import"),
        ("import tomli", False, "third-party"),
    ],
    "CPY005": [
        ("match x:\n    case 1: pass", True, "match/case"),
        ("x = 'match'", False, "match as name"),
    ],
    "CPY006": [
        ("asyncio.TaskGroup()", True, "TaskGroup"),
        ("asyncio.sleep(1)", False, "sleep is fine"),
    ],
    "CPY007": [
        ("import cgi", True, "removed"),
        ("import cgitb", True, "removed"),
        ("import json", False, "not removed"),
    ],
    "CPY019": [
        ("import distutils", True, "distutils"),
        ("from distutils.core import setup", True, "from distutils"),
        ("import setuptools", False, "replacement"),
    ],
    "CPY022": [
        ("x = ~True", True, "invert True"),
        ("x = ~False", True, "invert False"),
        ("x = not True", False, "logical not"),
        ("x = ~42", False, "int invert"),
    ],
    "CPY023": [
        ("import multiprocessing", True, "plain import"),
        (
            (
                "import multiprocessing\n"
                "multiprocessing.set_start_method('fork')"
            ),
            False,
            "explicit start",
        ),
    ],
    "CPY029": [
        ("d = locals()", True, "stored"),
        ("print(locals())", False, "debug print"),
        ("return locals()", False, "return"),
    ],
    "CPY036": [
        ("datetime.datetime.utcnow()", True, "deprecated"),
        ("datetime.datetime.now(tz=utc)", False, "correct"),
    ],
    "CPY037": [
        (
            "datetime.datetime.utcfromtimestamp(ts)",
            True,
            "deprecated",
        ),
        (
            "datetime.datetime.fromtimestamp(ts, tz)",
            False,
            "correct",
        ),
    ],
    "CPY038": [
        (
            "loop = asyncio.get_event_loop()",
            True,
            "old API",
        ),
        (
            "asyncio.run(main())",
            False,
            "correct",
        ),
        (
            "asyncio.get_running_loop()",
            False,
            "running loop fine",
        ),
        (
            (
                "import asyncio as aio\n"
                "loop = aio.get_event_loop()"
            ),
            False,
            "aliased module not caught",
        ),
        (
            "get_event_loop()",
            False,
            "bare call without module",
        ),
    ],
    "CPY041": [
        (
            "d = {'a': 1} | {'b': 2}",
            True,
            "dict literal merge",
        ),
        ("d |= other", True, "augmented assign"),
        ("x = a | b", False, "bare names"),
        ("flags = READ | WRITE", False, "bitflags"),
    ],
    "CPY046": [
        ("open('x.txt')", True, "no encoding"),
        (
            "open('x.txt', encoding='utf-8')",
            False,
            "explicit encoding",
        ),
        (
            "open('x.bin', 'rb')",
            False,
            "binary mode",
        ),
        (
            "open = my_open\nopen('x.txt')",
            True,
            "shadowed open still flagged",
        ),
        (
            "with open('x.txt') as f: pass",
            True,
            "context manager form",
        ),
    ],
    "CPY057": [
        ("pickle.dumps(obj)", True, "no protocol"),
        (
            "pickle.dumps(obj, None)",
            True,
            "protocol=None is default",
        ),
        (
            "pickle.dumps(obj, protocol=None)",
            True,
            "protocol=None keyword",
        ),
        ("pickle.dump(obj, f)", True, "dump no protocol"),
        (
            "pickle.Pickler(f)",
            True,
            "Pickler no protocol",
        ),
        (
            "pickle.dumps(obj, protocol=4)",
            False,
            "explicit protocol kw",
        ),
        (
            "pickle.dumps(obj, 4)",
            False,
            "positional protocol",
        ),
        (
            "pickle.loads(data)",
            False,
            "loads not flagged",
        ),
    ],
    "CPY009": [
        ("ExceptionGroup('test', [ValueError()])", True, "ExceptionGroup usage"),
        ("import os", False, "unrelated"),
    ],
    "CPY011": [
        ("from typing import Self", True, "Self requires 3.11+"),
        ("from typing import Optional", False, "Optional ok"),
    ],
    "CPY020": [
        ("import datetime\nx = datetime.UTC", True, "datetime.UTC"),
        ("import datetime\nx = datetime.timezone.utc", False, "timezone.utc ok"),
    ],
    "CPY026": [
        ("from typing.io import IO", True, "removed namespace"),
        ("from typing import IO", False, "correct form"),
    ],
    "CPY027": [
        ("import locale\nlocale.resetlocale()", True, "removed function"),
        ("locale.setlocale(locale.LC_ALL, '')", False, "correct form"),
    ],
    "CPY028": [
        ("import lib2to3", True, "removed module"),
        ("import libcst", False, "replacement"),
    ],
    "CPY033": [
        ("p.is_relative_to(base)", True, "is_relative_to"),
        ("p.is_absolute()", False, "other method"),
    ],
    "CPY034": [
        ("n.bit_count()", True, "bit_count"),
        ("n.bit_length()", False, "bit_length ok"),
    ],
    "CPY047": [
        ("from collections.abc import ByteString", True, "ByteString removed"),
        ("from collections.abc import Sequence", False, "Sequence ok"),
    ],
    "CPY048": [
        ("import concurrent.interpreters", True, "new module"),
        ("import concurrent.futures", False, "futures ok"),
    ],
    "CPY053": [
        ("from typing import get_overloads", True, "get_overloads import"),
        ("from typing import get_type_hints", False, "get_type_hints ok"),
    ],
    "CPY054": [
        ("class A:\n    def __trunc__(self): return 0", True, "__trunc__ defined"),
        ("class A:\n    def __int__(self): return 0", False, "__int__ ok"),
    ],
    "CPY055": [
        ("if NotImplemented: pass", True, "bool context"),
        ("return NotImplemented", False, "return ok"),
    ],
    "CPY062": [
        ("from string.templatelib import Template", True, "t-strings module"),
        ("from string import Template", False, "string.Template ok"),
    ],
    "CPY063": [
        ("import annotationlib", True, "annotationlib import"),
        ("import typing", False, "typing ok"),
    ],
    "PPY004": [
        ("import weakref\nref = weakref.proxy(obj)", True, "proxy usage"),
        ("ref = weakref.ref(obj)", False, "ref ok"),
    ],
    "PPY008": [
        ("import threading\n_local = threading.local()", True, "threading.local"),
        ("import threading\nt = threading.Thread()", False, "Thread ok"),
    ],
    "PPY009": [
        ("if id(x) == id(y): pass", True, "id comparison"),
        ("values.append(id(obj))", True, "retaining method"),
        ("cached_id = id(obj)", True, "stored id"),
        ("parent_map[id(child)] = parent", False, "dict key ok"),
        ("print(id(obj))", False, "transient arg ok"),
    ],
    "PPY013": [
        ("size = sys.getsizeof(obj)", True, "getsizeof"),
        ("size = len(obj)", False, "len ok"),
    ],
    "PPY021": [
        ("import socket\ns = socket.socket()", True, "socket not closed"),
    ],
    "PPY030": [
        ("import sys\nif sys.flags.hash_randomization: pass", True, "flags check"),
        ("if sys.flags.debug: pass", False, "debug flag ok"),
    ],
    "CPY010": [
        ("from dataclasses import dataclass\n@dataclass(slots=True)\nclass A: pass", True, "dataclass slots=True"),
        ("from dataclasses import dataclass\n@dataclass\nclass A: pass", False, "no slots"),
    ],
    "CPY012": [
        ("from typing import LiteralString", True, "LiteralString"),
        ("from typing import Optional", False, "Optional ok"),
    ],
    "CPY013": [
        ("from typing import override", True, "override"),
        ("from typing import overload", False, "overload ok"),
    ],
    "CPY014": [
        ("from typing import TypeAlias", True, "TypeAlias"),
        ("from typing import TypeVar", False, "TypeVar ok"),
    ],
    "CPY015": [
        ("from typing import Never", True, "Never"),
        ("from typing import Any", False, "Any ok"),
    ],
    "CPY016": [
        ("from typing import TypeVarTuple", True, "TypeVarTuple"),
        ("from typing import TypeVar", False, "TypeVar ok"),
    ],
    "CPY017": [
        ("from typing import Unpack", True, "Unpack"),
        ("from typing import Optional", False, "Optional ok"),
    ],
    "CPY018": [
        ("from typing import Required", True, "Required"),
        ("from typing import Optional", False, "Optional ok"),
    ],

    "CPY024": [
        ("from typing import TypeGuard", True, "TypeGuard"),
        ("from typing import Optional", False, "Optional ok"),
    ],
    "CPY025": [
        ("from typing import ParamSpec", True, "ParamSpec"),
        ("from typing import TypeVar", False, "TypeVar ok"),
    ],
    "CPY030": [
        ("import sys\nsys.path.append(b'/path')", True, "bytes on sys.path"),
        ("sys.path.append('/path')", False, "str ok"),
    ],
    "CPY031": [
        ("from typing import assert_never", True, "assert_never"),
        ("from typing import overload", False, "overload ok"),
    ],
    "CPY032": [
        ("from typing import reveal_type", True, "reveal_type"),
        ("from typing import cast", False, "cast ok"),
    ],
    "CPY035": [
        ("s.removeprefix('x')", True, "removeprefix"),
        ("s.replace('x', '')", False, "replace ok"),
    ],
    "CPY039": [
        ("import zoneinfo", True, "zoneinfo"),
        ("import datetime", False, "datetime ok"),
    ],
    "CPY040": [
        ("import graphlib", True, "graphlib"),
        ("import collections", False, "collections ok"),
    ],
    "CPY042": [
        ("x = aiter(obj)", True, "aiter builtin"),
        ("x = iter(obj)", False, "iter ok"),
    ],
    "CPY051": [
        ("_cache = []\ndef f():\n    _cache.append(1)", True, "unsynced mutation"),
        ("_cache = []\ndef f():\n    pass", False, "no mutation"),
    ],
    "PPY006": [
        ("list.custom = lambda: None", True, "monkey-patch builtin"),
        ("MyList.custom = lambda: None", False, "custom class ok"),
    ],
    "PPY010": [
        ("import gc\ngc.collect()", True, "gc.collect"),
        ("import gc\ngc.get_count()", False, "get_count ok"),
    ],
    "PPY011": [
        ("import array\narray.array('u', [])", True, "u typecode removed"),
        ("import array\narray.array('b', [])", False, "b typecode ok"),
    ],
    "PPY015": [
        ("def g():\n    try:\n        yield 1\n    finally: pass", True, "yield in try"),
        ("def g():\n    yield 1", False, "simple generator ok"),
    ],
    "PPY017": [
        ("class A: pass\nA.__del__ = fn", True, "add __del__ after class"),
        ("class A:\n    def __del__(self): pass", False, "__del__ in class ok"),
    ],
    "PPY018": [
        ("import sys\nsys.setrecursionlimit(1000)", True, "setrecursionlimit"),
        ("sys.getrecursionlimit()", False, "get ok"),
    ],
    "PPY019": [
        ("x = float('nan')", True, "nan identity"),
        ("x = float('inf')", False, "inf ok"),
    ],
    "PPY025": [
        ("list({1, 2, 3})", True, "set to list conversion"),
        ("list([1, 2, 3])", False, "list ok"),
    ],
    "PPY032": [
        ("d = {{1, 2}: 'a'}", True, "set used as dict key"),
        ("d = {frozenset([1]): 'a'}", False, "frozenset key ok"),
    ],
    "PPY041": [
        ("a = {}\nb = {}\nc = a | b", True, "dict merge pipe"),
        ("a = {}\nb = {}\na.update(b)", False, "update ok"),
    ],
    "PPY047": [
        ("from ctypes.util import find_library\nfind_library('ssl')", True, "find_library"),
        ("from ctypes import CDLL", False, "CDLL ok"),
    ],
    "CPY008": [
        ("class Base: pass\nclass Child(Base):\n    __slots__ = ['x']", True, "slots with non-slots base"),
        ("class A:\n    __slots__ = ['x']", False, "slots no base ok"),
    ],
    "CPY043": [
        ("import math\nmath.lcm(3, 4)", True, "math.lcm"),
        ("import math\nmath.gcd(3, 4)", False, "gcd ok"),
    ],
    "CPY044": [
        ("import math\nmath.gcd(3, 4, 5)", True, "gcd multi-arg"),
        ("import math\nmath.gcd(3, 4)", False, "gcd two-arg ok"),
    ],
    "CPY045": [
        ("h = hash(float('nan'))", True, "nan hash stored"),
        ("h = hash(1.5)", False, "float hash ok"),
    ],
    "CPY049": [
        ("import compression.zstd", True, "compression.zstd"),
        ("import zlib", False, "zlib ok"),
    ],
    "CPY050": [
        ("from pathlib import PurePath\np = PurePath('x')\np.is_reserved()", True, "is_reserved"),
        ("p.is_absolute()", False, "other method ok"),
    ],
    "PPY005": [
        ("f = open('x.txt', 'w')\nf.write(data)", True, "write without with"),
        ("with open('x.txt', 'w') as f:\n    f.write(data)", False, "with ok"),
    ],
    "PPY007": [
        ("import sys\nsys.intern('hello')", True, "intern"),
        ("sys.version", False, "other sys ok"),
    ],
    "PPY012": [
        ("class MyList(list):\n    def __getitem__(self, k): return k", True, "override builtin method"),
        ("class MyList(list): pass", False, "no override ok"),
    ],
    "PPY022": [
        ("import os\nos.environ['PYTHONHASHSEED'] = '0'", True, "hashseed env"),
        ("os.environ['PATH'] = '/usr'", False, "other env ok"),
    ],
    "PPY023": [
        ("import inspect\ninspect.ismethod(obj.method)", True, "ismethod"),
        ("inspect.isfunction(fn)", False, "isfunction ok"),
    ],
    "PPY024": [
        ("t = timer.timeit(1000)", True, "timeit result stored"),
        ("import timeit", False, "import only ok"),
    ],
    "PPY026": [
        ("isinstance(__builtins__, dict)", True, "builtins dict check"),
        ("import builtins", False, "import builtins ok"),
    ],
    "PPY027": [
        ("del os.path", True, "del module attr"),
        ("del local_var", False, "local del ok"),
    ],
    "PPY028": [
        ("import readline\nreadline.parse_and_bind('tab: complete')", True, "parse_and_bind"),
        ("readline.get_history_length()", False, "get ok"),
    ],
    "PPY029": [
        ("__builtins__ = {}", True, "assign to builtins"),
        ("builtins_copy = {}", False, "local var ok"),
    ],
    "PPY033": [
        ("class A:\n    def __del__(self):\n        raise ValueError('err')", True, "__del__ raises"),
        ("class A:\n    def __del__(self):\n        pass", False, "pass ok"),
    ],
    "PPY036": [
        ("open('f.txt', 'w', buffering=1)", True, "line buffering=1"),
        ("open('f.txt', 'w')", False, "no buffering ok"),
    ],
    "PPY037": [
        ("import os\nos.urandom(16)", True, "os.urandom"),
        ("import secrets\nsecrets.token_bytes(16)", False, "secrets ok"),
    ],
    "PPY039": [
        ("import os\nos.fork()", True, "os.fork"),
        ("os.getpid()", False, "getpid ok"),
    ],
    "PPY040": [
        ("subprocess.Popen(['cmd'], stdout=subprocess.PIPE)", True, "PIPE stdout"),
        ("subprocess.run(['cmd'])", False, "run ok"),
    ],
    "PPY042": [
        ("print('msg', flush=True)", True, "print flush"),
        ("print('msg')", False, "print ok"),
    ],
    "PPY044": [
        ("try:\n    x()\nexcept Exception as e:\n    pass\nprint(e)", True, "exception var used after handler"),
        ("try:\n    x()\nexcept Exception as e:\n    raise RuntimeError() from e", False, "used inside handler ok"),
    ],
    "PPY001": [
        (
            (
                "class A:\n"
                "    def __del__(self):\n"
                "        self.f.close()"
            ),
            True,
            "__del__ with call",
        ),
        (
            (
                "class A:\n"
                "    def __del__(self):\n"
                "        pass"
            ),
            False,
            "pass only",
        ),
    ],
    "PPY002": [
        (
            (
                "import ctypes\n"
                "ctypes.CDLL('libssl.so')"
            ),
            True,
            "ctypes.CDLL -- dangerous API",
        ),
        (
            "import ctypes",
            False,
            "import only - no use",
        ),
        (
            "import cffi",
            False,
            "cffi is ok",
        ),
    ],
    "PPY003": [
        ("sys.getrefcount(obj)", True, "getrefcount"),
        ("sys.version_info", False, "other sys"),
    ],

    "PPY014": [
        (
            (
                "s = ''\n"
                "for x in items:\n"
                "    s += x"
            ),
            True,
            "init+loop",
        ),
        (
            "s = ''.join(items)",
            False,
            "join safe",
        ),
    ],
    "PPY016": [
        (
            "keys = list(obj.__dict__)",
            True,
            "external __dict__ order-sensitive iteration",
        ),
        (
            "x = obj.__dict__",
            False,
            "plain external __dict__ access",
        ),
        (
            (
                "class A:\n"
                "    def f(self):\n"
                "        return self.__dict__"
            ),
            False,
            "self.__dict__ plain access",
        ),
        (
            (
                "class A:\n"
                "    def f(self):\n"
                "        return list(self.__dict__)"
            ),
            True,
            "self.__dict__ order-sensitive iteration",
        ),
    ],
    "PPY031": [
        (
            "if 257 is 257: pass",
            True,
            "large int literal",
        ),
        (
            "if x is None: pass",
            False,
            "None safe",
        ),
        (
            "if x is y: pass",
            False,
            "generic names",
        ),
    ],
    "PPY034": [
        ("h = hash(obj)", True, "stored hash"),
        (
            "if hash(x) == hash(y): pass",
            True,
            "compared hashes",
        ),
        (
            "d[hash(x)] = val",
            False,
            "hash as dict key",
        ),
        (
            (
                "def f():\n"
                "    h = hash(obj)"
            ),
            True,
            "stored hash in function",
        ),
        (
            "{hash(x): x for x in items}",
            False,
            "hash in dict comp key",
        ),
    ],
    "PPY035": [
        (
            "import numpy",
            True,
            "C ext",
        ),
        (
            "import json",
            False,
            "stdlib",
        ),
    ],
    "PPY038": [
        (
            "decimal.getcontext().prec = 50",
            True,
            "context modified",
        ),
        (
            "import decimal",
            False,
            "plain import",
        ),
    ],
    "PPY045": [
        (
            "sys.settrace(fn)",
            True,
            "settrace",
        ),
        (
            "sys.gettrace()",
            False,
            "gettrace fine",
        ),
    ],
    "CPY064": [
        ("import ast\nast.Num", True, "ast.Num"),
        ("import ast\nast.Constant", False, "ast.Constant ok"),
    ],
    "CPY065": [
        ("import pkgutil\npkgutil.find_loader('x')", True, "find_loader"),
        ("import importlib\nimportlib.util.find_spec('x')", False, "find_spec ok"),
    ],
    "CPY066": [
        ("from asyncio import ThreadedChildWatcher", True, "ThreadedChildWatcher"),
        ("import asyncio\nasyncio.Runner", False, "Runner ok"),
    ],
    "CPY067": [
        ("from typing import NamedTuple\nPoint = NamedTuple('Point', x=int, y=int)", True, "keyword syntax"),
        ("from typing import NamedTuple\nclass Point(NamedTuple):\n    x: int\n    y: int", False, "class syntax ok"),
    ],
    "CPY068": [
        ("from typing import no_type_check_decorator", True, "import decorator"),
        ("from typing import no_type_check", False, "no_type_check ok"),
    ],
    "CPY069": [
        ("import asyncio\nasyncio.iscoroutinefunction(func)", True, "asyncio.iscoroutinefunction"),
        ("import inspect\ninspect.iscoroutinefunction(func)", False, "inspect.iscoroutinefunction ok"),
    ],
    "CPY070": [
        ("import asyncio\nasyncio.get_event_loop_policy()", True, "get_event_loop_policy"),
        ("import asyncio\nasyncio.run(main())", False, "asyncio.run ok"),
    ],
    "CPY071": [
        ("import pty\npty.master_open()", True, "master_open"),
        ("import pty\npty.openpty()", False, "openpty ok"),
    ],
    "CPY072": [
        ("from importlib.abc import ResourceReader", True, "ResourceReader"),
        ("from importlib.resources.abc import TraversableResources", False, "importlib.resources.abc ok"),
    ],
    "CPY073": [
        ("import sqlite3\nsqlite3.version", True, "sqlite3.version"),
        ("import sqlite3\nsqlite3.sqlite_version", False, "sqlite_version ok"),
    ],
    "CPY074": [
        ("code_obj.__lnotab__", True, "__lnotab__"),
        ("code_obj.co_lines()", False, "co_lines ok"),
    ],
    "CPY075": [
        ("from http.server import CGIHTTPRequestHandler", True, "CGIHTTPRequestHandler"),
        ("from http.server import SimpleHTTPRequestHandler", False, "SimpleHTTPRequestHandler ok"),
    ],
    "CPY076": [
        ("import ssl\nssl.wrap_socket(sock)", True, "wrap_socket"),
        ("ctx = ssl.create_default_context()", False, "create_default_context ok"),
    ],
    "CPY077": [
        ("TypedDict('Name')", True, "zero-field form removed"),
        ("TypedDict('Name', None)", True, "None-field form removed"),
        ("TypedDict('Point', {'x': int})", False, "dict form still valid"),
        ("class Point(TypedDict):\n    x: int", False, "class form ok"),
    ],

    "PPY049": [
        ("import gc\ngc.collect()", True, "gc.collect"),
        ("import gc\ngc.get_threshold()", False, "get_threshold ok"),
    ],
    "PPY051": [
        ("code_obj.__lnotab__", True, "__lnotab__ pypy"),
        ("code_obj.co_linetable()", False, "co_linetable ok"),
    ],
    "PPY052": [
        ("from importlib.abc import ResourceReader", True, "ResourceReader pypy"),
        ("from importlib.resources.abc import TraversableResources", False, "resources.abc ok"),
    ],
    "PPY053": [
        ("@functools.lru_cache\ndef f(): pass", True, "lru_cache"),
        ("@functools.lru_cache(maxsize=128)\ndef f(): pass", True, "lru_cache with maxsize"),
    ],
}


def _validate_metadata(
    rule_id: str,
    findings,
    expected: dict[str, dict],
    failures: list[str],
) -> None:
    contract = expected.get(rule_id)

    if contract is None:
        return

    confidence = contract.get("confidence")
    evidence = contract.get("evidence")

    for finding in findings:
        if finding.confidence.value != confidence:
            failures.append(
                f"  {rule_id} metadata mismatch: "
                f"expected confidence={confidence!r}, "
                f"got {finding.confidence.value!r}"
            )

        if evidence.startswith("pep:"):
            expected_type = "pep"
        else:
            expected_type = evidence

        if finding.evidence_type.value != expected_type:
            failures.append(
                f"  {rule_id} metadata mismatch: "
                f"expected evidence_type={expected_type!r}, "
                f"got {finding.evidence_type.value!r}"
            )

        if finding.evidence_source != evidence:
            failures.append(
                f"  {rule_id} metadata mismatch: "
                f"expected evidence_source={evidence!r}, "
                f"got {finding.evidence_source!r}"
            )


def run() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    expected = load_expected()

    failures: list[str] = []
    total = 0
    correct = 0

    for rule_id, cases in sorted(GOLDEN.items()):
        rule = RULES.get(rule_id)

        if rule is None:
            failures.append(
                f"  MISSING RULE: {rule_id} not in ALL_RULES"
            )
            continue

        positive_cases = 0
        false_positives = 0

        for src, should_flag, label in cases:
            total += 1

            try:
                tree = ast.parse(src)
                findings = rule.check(
                    tree,
                    "<benchmark>",
                )
                did_flag = bool(findings)
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"  {rule_id} ERROR on '{label}': "
                    f"{type(exc).__name__}: {exc}"
                )
                continue

            if should_flag and did_flag:
                positive_cases += 1
            elif not should_flag and did_flag:
                false_positives += 1

            _validate_metadata(
                rule_id,
                findings,
                expected,
                failures,
            )

            if did_flag == should_flag:
                correct += 1
                if verbose:
                    print(
                        f"  [OK] {rule_id} '{label}'"
                    )
            else:
                kind = (
                    "FALSE POSITIVE"
                    if did_flag
                    else "FALSE NEGATIVE"
                )

                failures.append(
                    f"  {rule_id} [{kind}] "
                    f"'{label}' expected={should_flag} "
                    f"got={len(findings)} findings"
                )

        contract = expected.get(rule_id)

        if contract is not None:
            min_tp = int(
                contract.get("min_true_positives", 0)
            )
            max_fp = int(
                contract.get("max_false_positives", 0)
            )

            if positive_cases < min_tp:
                failures.append(
                    f"  {rule_id} quality contract failed: "
                    f"true-positive cases={positive_cases} "
                    f"< minimum={min_tp}"
                )

            if false_positives > max_fp:
                failures.append(
                    f"  {rule_id} quality contract failed: "
                    f"false-positive cases={false_positives} "
                    f"> maximum={max_fp}"
                )

    coverage = (
        len(GOLDEN) / len(RULES) * 100
        if RULES
        else 0
    )

    print(
        f"pyrift benchmark: {correct}/{total} cases correct "
        f"({100 * correct // total if total else 0}%)"
    )
    print(
        f"Golden rule coverage: "
        f"{len(GOLDEN)}/{len(RULES)} "
        f"({coverage:.1f}%)"
    )

    if coverage < 50:
        print(
            "[WARN] Golden benchmark covers less than 50% "
            "of the rule inventory."
        )

    if failures:
        print(
            f"\n[FAIL] {len(failures)} failure(s):"
        )
        for failure in failures:
            print(failure)
        return 1

    print("[OK] All reviewed benchmark contracts passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())