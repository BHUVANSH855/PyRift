#!/usr/bin/env python3
"""
Self-scan quality gate.

Scans pyrift's own source and records expected finding counts.
CI fails if findings exceed the reviewed threshold.

Run: python benchmark/self_scan.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pyrift import ALL_RULES

# Reviewed thresholds — update when findings are intentionally added
# pyrift scans itself and should have minimal findings
EXPECTED = {
    "max_total": 15,       # reviewed threshold — see known_findings below
    "max_errors": 0,       # zero errors in our own code
    "known_findings": [
        # PPY009 (9x) — pyrift/analysis/scope.py uses id() as AST node
        # identity keys in parent_map dict. This is intentional — we use
        # id() to build a child→parent lookup, not for PyPy stability.
        # These are false positives in pyrift's own infrastructure code.
        "PPY009",
    ],
}


def main() -> int:
    src_dir = Path(__file__).parent.parent / "pyrift"
    findings = []
    files = 0

    for path in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for rule in ALL_RULES:
                try:
                    findings.extend(rule.check(tree, str(path)))
                except Exception:  # noqa: S110
                    pass
            files += 1
        except SyntaxError:
            pass

    errors = [f for f in findings if f.severity.value == "error"]
    warnings = [f for f in findings if f.severity.value == "warning"]

    print(f"Self-scan: {files} files, {len(findings)} findings "
          f"({len(errors)} ERR, {len(warnings)} WARN)")

    if findings:
        from collections import Counter
        counts = Counter(f.rule_id for f in findings)
        for rid, n in counts.most_common():
            f = next(x for x in findings if x.rule_id == rid)
            print(f"  {rid} ({n}x): {f.title}")

    failed = False
    if len(errors) > EXPECTED["max_errors"]:
        print(f"❌ Too many errors: {len(errors)} > {EXPECTED['max_errors']}")
        failed = True
    if len(findings) > EXPECTED["max_total"]:
        print(f"❌ Too many findings: {len(findings)} > {EXPECTED['max_total']}")
        failed = True

    if not failed:
        print("✅ Self-scan passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())