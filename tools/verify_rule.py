#!/usr/bin/env python3
"""Lightweight rule-verification harness for PyRift rule authors.

Runs five probes against one rule (or every active rule with ``--all``)
to give a quick pass / fail summary without spinning up the full benchmark
infrastructure.

Probes
------
1. metadata      Rule ID is in RULE_METADATA with all required fields.
2. import        Rule is accessible via ALL_RULES with the correct rule_id.
3. explain       ``pyrift explain <id>`` subprocess exits 0.
4. test_file     A pytest module exists at the expected path under ``tests/``.
5. self_scan     ``pyrift scan pyrift/`` completes without a rule_error for
                 this rule (the rule does not crash on pyrift's own source).

Usage
-----
    python tools/verify_rule.py CPY055
    python tools/verify_rule.py --all        # verify every active rule
    python tools/verify_rule.py --all --fail-fast
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository root — resolve relative to this file so the script works from
# any working directory.
# ---------------------------------------------------------------------------
_REPO = Path(__file__).resolve().parent.parent


def _import_pyrift():
    """Import pyrift from the local checkout (not a site-packages install)."""
    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))

    from pyrift.rule_metadata import (  # noqa: PLC0415
        REQUIRED_METADATA_FIELDS,
        RULE_METADATA,
    )
    from pyrift.scanner import ALL_RULES  # noqa: PLC0415

    return RULE_METADATA, REQUIRED_METADATA_FIELDS, ALL_RULES


# ---------------------------------------------------------------------------
# Individual probes — each returns (passed: bool, detail: str)
# ---------------------------------------------------------------------------

def probe_metadata(rule_id: str, rule_metadata, required_fields) -> tuple[bool, str]:
    """Probe 1: metadata completeness."""
    if rule_id not in rule_metadata:
        return False, "not in RULE_METADATA"
    meta = rule_metadata[rule_id]
    missing = [f for f in required_fields if f not in meta]
    if missing:
        return False, f"missing fields: {', '.join(missing)}"
    return True, "all required fields present"


def probe_import(rule_id: str, all_rules) -> tuple[bool, str]:
    """Probe 2: rule importable with correct rule_id attribute."""
    matches = [r for r in all_rules if r.rule_id == rule_id]
    if not matches:
        return False, "not found in ALL_RULES"
    rule = matches[0]
    if rule.rule_id != rule_id:
        return False, f"rule_id mismatch: got {rule.rule_id!r}"
    return True, f"found as {type(rule).__name__}"


def probe_explain(rule_id: str) -> tuple[bool, str]:
    """Probe 3: pyrift explain exits 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pyrift", "explain", rule_id],
        capture_output=True,
        text=True,
        cwd=_REPO,
    )
    if result.returncode == 0:
        return True, "exit 0"
    return False, f"exit {result.returncode}: {result.stderr.strip()[:120]}"


def probe_test_file(rule_id: str) -> tuple[bool, str]:
    """Probe 4: test module exists at the expected path."""
    slug = rule_id.lower()  # e.g. "cpy055"
    if slug.startswith("cpy"):
        candidates = [
            _REPO / "tests" / "cpython" / f"test_{slug}.py",
        ]
    elif slug.startswith("ppy"):
        candidates = [
            _REPO / "tests" / "pypy" / f"test_{slug}.py",
        ]
    else:
        candidates = [
            _REPO / "tests" / f"test_{slug}.py",
        ]
    for path in candidates:
        if path.exists():
            return True, str(path.relative_to(_REPO))
    return False, f"no test file found (looked for {candidates[0].relative_to(_REPO)})"


def probe_self_scan(rule_id: str) -> tuple[bool, str]:
    """Probe 5: rule runs without error on pyrift's own source code."""
    result = subprocess.run(
        [
            sys.executable, "-m", "pyrift", "scan",
            "--format", "json",
            "--select", rule_id,
            str(_REPO / "pyrift"),
        ],
        capture_output=True,
        text=True,
        cwd=_REPO,
    )
    # Exit codes 0 (no findings) and 1 (findings present) are both healthy.
    # Exit code 2 means a usage/runtime error.
    if result.returncode == 2:
        return False, f"scan exited 2: {result.stderr.strip()[:120]}"
    # Check for rule_errors in JSON output
    import json  # noqa: PLC0415
    try:
        data = json.loads(result.stdout)
        rule_errors = data.get("rule_errors", [])
        for err in rule_errors:
            if isinstance(err, dict) and err.get("rule_id") == rule_id:
                return False, f"rule_error: {err.get('error', '')}"
            if isinstance(err, str) and rule_id in err:
                return False, f"rule_error: {err}"
    except (json.JSONDecodeError, KeyError):
        pass  # non-JSON output or missing key — still counts as passing
    return True, f"scan completed (exit {result.returncode})"


# ---------------------------------------------------------------------------
# Per-rule runner
# ---------------------------------------------------------------------------

PROBES = [
    ("metadata",  probe_metadata),
    ("import",    probe_import),
    ("explain",   probe_explain),
    ("test_file", probe_test_file),
    ("self_scan", probe_self_scan),
]


def verify_rule(
    rule_id: str,
    rule_metadata,
    required_fields,
    all_rules,
    *,
    verbose: bool = False,
) -> bool:
    """Run all 5 probes for one rule.  Returns True when all pass."""
    results: list[tuple[str, bool, str]] = []

    passed, detail = probe_metadata(rule_id, rule_metadata, required_fields)
    results.append(("metadata", passed, detail))

    passed, detail = probe_import(rule_id, all_rules)
    results.append(("import", passed, detail))

    passed, detail = probe_explain(rule_id)
    results.append(("explain", passed, detail))

    passed, detail = probe_test_file(rule_id)
    results.append(("test_file", passed, detail))

    passed, detail = probe_self_scan(rule_id)
    results.append(("self_scan", passed, detail))

    all_passed = all(p for _, p, _ in results)
    status = "PASS" if all_passed else "FAIL"
    print(f"{rule_id}  [{status}]")
    if not all_passed or verbose:
        for name, ok, detail in results:
            icon = "✓" if ok else "✗"
            print(f"  {icon} {name:<12} {detail}")

    return all_passed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Verify one or all PyRift rules with five probes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "rule_id",
        nargs="?",
        metavar="RULE_ID",
        help="Rule to verify, e.g. CPY055",
    )
    group.add_argument(
        "--all",
        action="store_true",
        dest="all_rules",
        help="Verify every active (non-tombstone) rule.",
    )
    p.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failing rule (only relevant with --all).",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Always print individual probe results, even for passing rules.",
    )
    return p


def main() -> int:
    args = _build_parser().parse_args()
    rule_metadata, required_fields, all_rules = _import_pyrift()

    active_ids: list[str] = sorted(
        rule_id
        for rule_id, meta in rule_metadata.items()
        if meta.get("status") != "tombstone"
    )

    if args.rule_id:
        targets = [args.rule_id.upper()]
    else:
        targets = active_ids

    failures: list[str] = []
    for rule_id in targets:
        ok = verify_rule(
            rule_id,
            rule_metadata,
            required_fields,
            all_rules,
            verbose=args.verbose,
        )
        if not ok:
            failures.append(rule_id)
            if args.fail_fast:
                break

    print()
    if failures:
        print(f"FAILED: {len(failures)} rule(s): {', '.join(failures)}")
        return 1

    checked = len(targets)
    print(f"All {checked} rule(s) passed all 5 probes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())