#!/usr/bin/env python3
"""
Real project corpus benchmark.

Scans reviewed real-world Python packages.

Normal usage:
    python benchmark/corpus.py

Strict CI mode:
    PYRIFT_CORPUS_STRICT=1 python benchmark/corpus.py
"""
from __future__ import annotations

import ast
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrift import ALL_RULES
from pyrift.finding import Runtime

STRICT = os.environ.get("PYRIFT_CORPUS_STRICT") == "1"


CORPUS = {
    "requests": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 35,
        "max_errors": 2,
        "rules": {
            "PPY044": 6,
            "PPY015": 4,
            "PPY035": 2,
            "PPY008": 1,
            "PPY037": 1,
            "CPY052": 1,
            "PPY016": 1,
            "PPY012": 1,
        },
    },
    "flask": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 60,
        "max_errors": 10,
        "rules": {},
    },
    "asyncio": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 120,
        "max_errors": 20,
        "rules": {
            "PPY033": 14,
            "PPY044": 13,
            "CPY008": 11,
            "PPY001": 9,
            "PPY021": 6,
            "CPY009": 4,
            "CPY041": 3,
            "PPY014": 2,
            "PPY005": 1,
            "CPY051": 1,
        },
    },
    "email": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 60,
        "max_errors": 10,
        "rules": {
            "PPY014": 8,
            "CPY051": 5,
            "PPY027": 4,
            "PPY016": 2,
            "PPY012": 2,
            "CPY035": 2,
        },
    },
    "httpx": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 40,
        "max_errors": 5,
        "rules": {
            "PPY015": 9,
            "PPY014": 2,
            "PPY037": 2,
            "CPY029": 1,
        },
    },
    "logging": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 40,
        "max_errors": 5,
        "rules": {
            "PPY016": 11,
            "PPY021": 5,
            "PPY012": 3,
            "PPY014": 1,
        },
    },
    "http": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 30,
        "max_errors": 10,
        "rules": {
            "CPY020": 4,
            "PPY012": 3,
            "PPY039": 1,
            "PPY040": 1,
            "PPY044": 1,
            "PPY015": 1,
            "CPY046": 1,
            "PPY016": 1,
        },
    },
}


def scan_package(
    name: str,
    runtime: Runtime,
) -> tuple[int, Counter[str], int, int]:
    """Return files, per-rule counts, errors, and rule errors."""

    try:
        module = __import__(name)
        pkg_file = getattr(module, "__file__", None)

        if pkg_file is None:
            return 0, Counter(), 0, 0

        pkg_dir = Path(pkg_file).parent
    except (ImportError, AttributeError):
        return 0, Counter(), 0, 0

    counts: Counter[str] = Counter()
    files = 0
    errors = 0
    rule_errors = 0

    for path in pkg_dir.rglob("*.py"):
        try:
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
        except SyntaxError:
            continue

        files += 1

        for rule in ALL_RULES:
            try:
                findings = rule.check(
                    tree,
                    str(path),
                )
            except Exception as exc:  # noqa: BLE001
                print(
                    f"Rule {rule.rule_id} failed for {path}: {exc}",
                )
                rule_errors += 1
                continue

            for finding in findings:
                if finding.runtime not in (
                    runtime,
                    Runtime.BOTH,
                ):
                    continue

                counts[finding.rule_id] += 1

                if finding.severity.value == "error":
                    errors += 1

    return files, counts, errors, rule_errors


def main() -> int:
    print("Real project corpus benchmark")
    print("=" * 50)

    failed = False

    for package, limits in CORPUS.items():
        runtime = limits["runtime"]

        files, counts, errors, rule_errors = scan_package(
            package,
            runtime,
        )

        if files == 0:
            message = (
                f"  {package}: not installed"
            )

            if STRICT:
                print(message + " -- [FAIL]")
                failed = True
            else:
                print(message + " -- skipping")

            continue

        total = sum(counts.values())

        status = "[OK]"

        if total > limits["max_findings"]:
            status = "[FAIL]"
            failed = True

        if errors > limits["max_errors"]:
            status = "[FAIL]"
            failed = True

        if rule_errors:
            status = "[FAIL]"
            failed = True

        print(
            f"  {status} {package}: "
            f"{files} files, "
            f"{total} findings "
            f"({errors} ERR)"
        )

        if total > limits["max_findings"]:
            print(
                f"     Too many findings: "
                f"{total} > {limits['max_findings']}"
            )

        if errors > limits["max_errors"]:
            print(
                f"     Too many errors: "
                f"{errors} > {limits['max_errors']}"
            )

        if rule_errors:
            print(
                f"     Rule execution errors: "
                f"{rule_errors}"
            )

        for rule_id, maximum in limits["rules"].items():
            actual = counts.get(rule_id, 0)

            if actual > maximum:
                print(
                    f"     Rule regression: {rule_id}: "
                    f"{actual} > {maximum}"
                )
                failed = True

    print()

    if failed:
        print(
            "[FAIL] Corpus benchmark failed -- "
            "precision regression detected."
        )
        return 1

    print("[OK] Corpus benchmark passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())