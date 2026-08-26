#!/usr/bin/env python3
"""
Self-scan quality gate.

Scans pyrift's own source using the production scanner.

The gate fails when:
- source files cannot be parsed;
- any rule crashes;
- unexpected finding types appear;
- unexpected finding counts appear.

Run:
    python benchmark/self_scan.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrift.scanner import scan

# Exact reviewed findings expected from pyrift's own source.
#
# An empty mapping intentionally means that any new self-finding must
# be reviewed before CI is allowed to pass.
EXPECTED_RULE_COUNTS: dict[str, int] = {}


def main() -> int:
    src_dir = Path(__file__).parent.parent / "pyrift"

    result = scan(
        src_dir,
        use_project_config=False,
    )

    print(
        f"Self-scan: {result.files_scanned} files scanned, "
        f"{len(result.findings)} findings, "
        f"{len(result.rule_errors)} rule execution errors"
    )

    failed = False

    if result.rule_errors:
        print(
            f"[FAIL] {len(result.rule_errors)} rule execution "
            "error(s) detected."
        )
        for error in result.rule_errors:
            print(f"  {error}")
        failed = True

    actual = Counter(
        finding.rule_id
        for finding in result.findings
    )

    expected = Counter(EXPECTED_RULE_COUNTS)

    for rule_id in sorted(set(actual) | set(expected)):
        actual_count = actual.get(rule_id, 0)
        expected_count = expected.get(rule_id, 0)

        if actual_count != expected_count:
            print(
                f"[FAIL] {rule_id}: "
                f"expected {expected_count}, "
                f"found {actual_count}"
            )
            failed = True

    if not result.findings:
        print("[OK] No self-findings detected.")

    if failed:
        print("[FAIL] Self-scan quality gate failed.")
        return 1

    print("[OK] Self-scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())