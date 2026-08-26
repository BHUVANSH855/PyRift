#!/usr/bin/env python3
"""
Real project corpus benchmark.

Scans major real-world Python packages and records expected finding ranges.
CI fails if findings exceed reviewed thresholds (regression detection).

Run: python benchmark/corpus.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pyrift import ALL_RULES

# Reviewed finding ranges per package
# Update when rules change and findings are re-reviewed
# Reviewed on 2026-08-26 against pyrift v0.8.0
# All findings manually verified as genuine compatibility issues
CORPUS = {
    "requests": {"max_findings": 35,  "max_errors": 2},
    "flask":    {"max_findings": 60,  "max_errors": 10},
    "asyncio":  {"max_findings": 120, "max_errors": 20},
    "email":    {"max_findings": 60,  "max_errors": 10},
}


def scan_package(name: str) -> tuple[int, int, int]:
    """Returns (files, findings, errors)."""
    try:
        mod = __import__(name)
        pkg_dir = Path(mod.__file__).parent
    except (ImportError, AttributeError):
        return 0, 0, 0

    findings = []
    files = 0
    for path in pkg_dir.rglob("*.py"):
        try:
            tree = ast.parse(
                path.read_text(encoding="utf-8", errors="replace")
            )
            for rule in ALL_RULES:
                try:
                    findings.extend(rule.check(tree, str(path)))
                except Exception:  # noqa: S110
                    pass
            files += 1
        except SyntaxError:
            pass

    errors = sum(1 for f in findings if f.severity.value == "error")
    return files, len(findings), errors


def main() -> int:
    print("Real project corpus benchmark")
    print("=" * 50)
    failed = False

    for pkg, limits in CORPUS.items():
        files, total, errors = scan_package(pkg)
        if files == 0:
            print(f"  {pkg}: not installed — skipping")
            continue

        status = "✅" if (
            total <= limits["max_findings"] and
            errors <= limits["max_errors"]
        ) else "❌"

        print(f"  {status} {pkg}: {files} files, "
              f"{total} findings ({errors} ERR) "
              f"[max={limits['max_findings']}]")

        if total > limits["max_findings"]:
            print(f"     Too many findings: {total} > {limits['max_findings']}")
            failed = True
        if errors > limits["max_errors"]:
            print(f"     Too many errors: {errors} > {limits['max_errors']}")
            failed = True

    print()
    if failed:
        print("❌ Corpus benchmark failed — rule precision regression detected.")
        return 1
    print("✅ Corpus benchmark passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())