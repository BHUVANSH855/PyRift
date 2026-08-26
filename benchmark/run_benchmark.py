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
    "PPY013": [
        ("size = sys.getsizeof(obj)", True, "getsizeof"),
        ("sys.version", False, "other sys"),
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
            "x = obj.__dict__",
            True,
            "external __dict__",
        ),
        (
            (
                "class A:\n"
                "    def f(self):\n"
                "        return self.__dict__"
            ),
            False,
            "self.__dict__ in method",
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

            if should_flag:
                positive_cases += 1
            elif did_flag:
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