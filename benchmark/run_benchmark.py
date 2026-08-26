#!/usr/bin/env python3
"""
pyrift golden benchmark runner.

Tests every rule against known positive and negative cases.
Fails (exit 1) on any false positive — this is the CI precision gate.

Usage:
    python benchmark/run_benchmark.py
    python benchmark/run_benchmark.py --verbose
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pyrift import ALL_RULES

RULES = {r.rule_id: r for r in ALL_RULES}

# Golden test cases: (source, should_flag, label)
# Every rule must have at least 1 positive and 1 negative case.
GOLDEN = {
    "CPY001": [
        ("d.keys() == ['a', 'b']",              True,  "keys vs list"),
        ("set(d.keys()) == {'a', 'b'}",          False, "set comparison safe"),
        ("d.keys() == other.keys()",              False, "two key views"),
    ],
    "CPY002": [
        ("e.add_note('hint')",                   True,  "add_note call"),
        ("e.args",                               False, "other attr"),
    ],
    "CPY003": [
        ("isinstance(x, int | str)",             True,  "union in isinstance"),
        ("x: int | str = 1",                     False, "annotation only"),
    ],
    "CPY004": [
        ("import tomllib",                       True,  "tomllib import"),
        ("import tomli",                         False, "third-party"),
    ],
    "CPY005": [
        ("match x:\n    case 1: pass",           True,  "match/case"),
        ("x = 'match'",                          False, "match as name"),
    ],
    "CPY006": [
        ("asyncio.TaskGroup()",                  True,  "TaskGroup"),
        ("asyncio.sleep(1)",                     False, "sleep is fine"),
    ],
    "CPY007": [
        ("import cgi",                           True,  "removed"),
        ("import cgitb",                         True,  "removed"),
        ("import json",                          False, "not removed"),
    ],
    "CPY019": [
        ("import distutils",                     True,  "distutils"),
        ("from distutils.core import setup",     True,  "from distutils"),
        ("import setuptools",                    False, "replacement"),
    ],
    "CPY022": [
        ("x = ~True",                            True,  "invert True"),
        ("x = ~False",                           True,  "invert False"),
        ("x = not True",                         False, "logical not"),
        ("x = ~42",                              False, "int invert"),
    ],
    "CPY023": [
        ("import multiprocessing",               True,  "plain import"),
        ("import multiprocessing\nmultiprocessing.set_start_method('fork')",
                                                 False, "explicit start"),
    ],
    "CPY029": [
        ("d = locals()",                         True,  "stored"),
        ("print(locals())",                      False, "debug print"),
        ("return locals()",                      False, "return"),
    ],
    "CPY036": [
        ("datetime.datetime.utcnow()",           True,  "deprecated"),
        ("datetime.datetime.now(tz=utc)",        False, "correct"),
    ],
    "CPY037": [
        ("datetime.datetime.utcfromtimestamp(ts)", True, "deprecated"),
        ("datetime.datetime.fromtimestamp(ts, tz)", False, "correct"),
    ],
    "CPY038": [
        ("loop = asyncio.get_event_loop()",      True,  "old API"),
        ("asyncio.run(main())",                  False, "correct"),
        ("asyncio.get_running_loop()",           False, "running loop fine"),
    ],
    "CPY041": [
        ("d = {'a': 1} | {'b': 2}",             True,  "dict literal merge"),
        ("d |= other",                           True,  "augmented assign"),
        ("x = a | b",                            False, "bare names"),
        ("flags = READ | WRITE",                 False, "bitflags"),
    ],
    "CPY046": [
        ("open('x.txt')",                        True,  "no encoding"),
        ("open('x.txt', encoding='utf-8')",      False, "explicit encoding"),
        ("open('x.bin', 'rb')",                  False, "binary"),
    ],
    "CPY057": [
        ("pickle.dumps(obj)",                    True,  "no protocol"),
        ("pickle.dumps(obj, protocol=4)",        False, "explicit protocol"),
        ("pickle.dumps(obj, 4)",                 False, "positional protocol"),
        ("pickle.loads(data)",                   False, "loads not flagged"),
    ],
    "PPY001": [
        ("class A:\n    def __del__(self):\n        self.f.close()", True, "__del__ with call"),
        ("class A:\n    def __del__(self):\n        pass", False, "pass only"),
    ],
    "PPY002": [
        ("import ctypes\nctypes.CDLL('libssl.so')", True, "ctypes.CDLL — dangerous API"),
        ("import ctypes", False, "import only - no use"),
        ("import cffi", False, "cffi is ok"),
    ],
    "PPY003": [
        ("sys.getrefcount(obj)",                 True,  "getrefcount"),
        ("sys.version_info",                     False, "other sys"),
    ],
    "PPY013": [
        ("size = sys.getsizeof(obj)",            True,  "getsizeof"),
        ("sys.version",                          False, "other sys"),
    ],
    "PPY014": [
        ("s = ''\nfor x in items:\n    s += x", True,  "init+loop"),
        ("s = ''.join(items)",                   False, "join safe"),
    ],
    "PPY016": [
        ("x = obj.__dict__",                     True,  "external __dict__"),
        ("class A:\n    def f(self):\n        return self.__dict__", False, "self.__dict__ in method"),
    ],
    "PPY031": [
        ("if 257 is 257: pass",                  True,  "large int literal"),
        ("if x is None: pass",                   False, "None safe"),
        ("if x is y: pass",                      False, "generic names"),
    ],
    "PPY034": [
        ("h = hash(obj)",                        True,  "stored hash"),
        ("if hash(x) == hash(y): pass",          True,  "compared"),
        ("d[hash(x)] = val",                     False, "as dict key"),
    ],
    "PPY035": [
        ("import numpy",                         True,  "C ext"),
        ("import json",                          False, "stdlib"),
    ],
    "PPY038": [
        ("decimal.getcontext().prec = 50",       True,  "context modified"),
        ("import decimal",                       False, "plain import"),
    ],
    "PPY045": [
        ("sys.settrace(fn)",                     True,  "settrace"),
        ("sys.gettrace()",                       False, "gettrace fine"),
    ],
}


def run() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    failures = []
    total = correct = 0

    for rule_id, cases in sorted(GOLDEN.items()):
        rule = RULES.get(rule_id)
        if rule is None:
            failures.append(f"  MISSING RULE: {rule_id} not in ALL_RULES")
            continue

        for src, should_flag, label in cases:
            total += 1
            try:
                tree = ast.parse(src)
                findings = rule.check(tree, "<benchmark>")
                did_flag = len(findings) > 0
            except Exception as e:
                failures.append(f"  {rule_id} ERROR on '{label}': {e}")
                continue

            if did_flag == should_flag:
                correct += 1
                if verbose:
                    print(f"  ✅ {rule_id} '{label}'")
            else:
                kind = "FALSE POSITIVE" if did_flag else "FALSE NEGATIVE"
                failures.append(
                    f"  {rule_id} [{kind}] '{label}' "
                    f"expected={should_flag} got={len(findings)} findings"
                )

    print(f"pyrift benchmark: {correct}/{total} cases correct "
          f"({100 * correct // total}%)")

    if failures:
        print(f"\n❌ {len(failures)} failure(s):")
        for f in failures:
            print(f)
        return 1

    print("✅ All benchmark cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run())