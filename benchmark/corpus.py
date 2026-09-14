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

import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrift import scan
from pyrift.finding import Runtime

STRICT = os.environ.get("PYRIFT_CORPUS_STRICT") == "1"


CORPUS = {
    # Note on PPY035 (2026-09-14, review point 18): scanning pydantic
    # with runtime=Runtime.BOTH (i.e. without the CPython-only filter
    # applied below) surfaces 44 separate PPY035 findings, essentially
    # one per pydantic-core call site -- confirmed by direct measurement
    # against pydantic 2.13.5, not estimated. That's real-world evidence
    # for the review's exact critique: "imports a C extension" is too
    # broad a signal to treat as a single meaningful finding per
    # call-site. PPY035's confidence was downgraded to MEDIUM in
    # rule_metadata.py as an interim measure; narrowing the detector
    # itself (to fire once per package rather than per call site, or to
    # require an actual CPython-only API) is tracked as future work in
    # DELIVERY_NOTES.md, section 18. The `pydantic` entry below uses
    # Runtime.CPYTHON like the rest of this corpus, so it does not
    # surface this by default -- re-run with runtime=Runtime.BOTH
    # locally to reproduce it.
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
            # Current reviewed stdlib corpus produces three CPY035 findings.
            "CPY035": 3,
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
    "urllib": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 20,
        "max_errors": 0,
        "rules": {
            "CPY008": 8,
            "CPY051": 1,
        },
    },
    "json": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 5,
        "max_errors": 0,
        "rules": {},
    },
    "collections": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 10,
        "max_errors": 3,
        "rules": {
            "CPY035": 2,
            "CPY041": 1,
        },
    },
    # --- Added 2026-09-14 (review section 79: "measure findings/KLOC,
    # false positives/KLOC on real packages" -- picking three more from
    # the review's own suggested list, prioritizing ones that actually
    # exercise the new guard/shim suppression on real code). ---
    "packaging": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 15,
        "max_errors": 6,
        "rules": {
            "CPY008": 8,
            "CPY009": 5,
        },
    },
    "click": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 10,
        "max_errors": 4,
        "rules": {
            "CPY046": 5,
            "CPY008": 2,
            "CPY051": 2,
        },
    },
    "pydantic": {
        "runtime": Runtime.CPYTHON,
        "max_findings": 40,
        "max_errors": 4,
        "rules": {
            "CPY008": 30,
            "CPY039": 3,
            "CPY051": 3,
            "CPY046": 2,
        },
    },
}


def scan_package(
    name: str,
    runtime: Runtime,
) -> tuple[int, Counter[str], int, int, int, dict[str, int]]:
    """Scan an installed package's source tree and return files, per-rule
    counts, errors, rule errors, guard-suppressed count, and a
    confidence breakdown.

    Uses ``pyrift.scan()`` -- the same entry point the CLI uses -- rather
    than calling ``rule.check()`` directly in a hand-rolled loop. This
    matters: a hand-rolled loop bypasses the guard/implementation-shim
    suppression pass in ``scanner.py`` (see ``pyrift.analysis.guards``),
    which means a corpus benchmark built that way would never actually
    exercise -- or catch a regression in -- the exact false-positive
    filtering this benchmark exists to validate.
    """
    try:
        module = __import__(name)
        pkg_file = getattr(module, "__file__", None)

        if pkg_file is None:
            return 0, Counter(), 0, 0, 0, {}

        pkg_dir = Path(pkg_file).parent
    except (ImportError, AttributeError):
        return 0, Counter(), 0, 0, 0, {}

    result = scan(pkg_dir, use_project_config=False)

    counts: Counter[str] = Counter()
    errors = 0
    breakdown = {
        "high_confidence": 0,
        "medium_confidence": 0,
        "informational": 0,
        "analyzer_errors": len(result.rule_errors),
    }

    for finding in result.findings:
        if finding.runtime not in (runtime, Runtime.BOTH):
            continue

        counts[finding.rule_id] += 1

        if finding.severity.value == "error":
            errors += 1

        # Computed from the same runtime-filtered findings as `counts`
        # above -- ScanResult.breakdown() deliberately does not filter
        # by runtime (it's a whole-scan summary), so using it directly
        # here would silently mix in PyPy-only findings when reporting
        # a CPython-runtime corpus package and vice versa.
        if finding.confidence.value == "high":
            breakdown["high_confidence"] += 1
        elif finding.confidence.value == "medium":
            breakdown["medium_confidence"] += 1
        else:
            breakdown["informational"] += 1

    return (
        result.files_scanned,
        counts,
        errors,
        len(result.rule_errors),
        result.guard_suppressed,
        breakdown,
    )


def _installed_version(name: str) -> str:
    """Best-effort installed package version, for reproducibility
    (2026-09 review, point 6): corpus results are only meaningful
    alongside the exact package version they were measured against,
    since findings/KLOC will legitimately drift as a dependency's own
    source changes across releases -- that's not a pyrift regression.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version(name)
    except PackageNotFoundError:
        return "stdlib/unknown"


def main() -> int:
    print("Real project corpus benchmark")
    print("=" * 50)

    failed = False
    total_guard_suppressed = 0
    total_findings_all_packages = 0
    total_high_confidence = 0

    for package, limits in CORPUS.items():
        runtime = limits["runtime"]

        (
            files,
            counts,
            errors,
            rule_errors,
            guard_suppressed,
            breakdown,
        ) = scan_package(package, runtime)

        if files == 0:
            message = f"  {package}: not installed"

            if STRICT:
                print(message + " -- [FAIL]")
                failed = True
            else:
                print(message + " -- skipping")

            continue

        total = sum(counts.values())
        pkg_version = _installed_version(package)

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

        total_guard_suppressed += guard_suppressed
        total_findings_all_packages += total
        total_high_confidence += breakdown.get("high_confidence", 0)

        print(
            f"  {status} {package} ({pkg_version}): "
            f"{files} files, "
            f"{total} findings "
            f"({errors} ERR, {rule_errors} rule-errors, "
            f"{guard_suppressed} guard/shim-suppressed)"
        )
        print(
            "        confidence breakdown: "
            f"high={breakdown.get('high_confidence', 0)} "
            f"medium={breakdown.get('medium_confidence', 0)} "
            f"info={breakdown.get('informational', 0)}"
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
            print(f"     {rule_errors} rule execution error(s)")

        for rule_id, maximum in limits["rules"].items():
            actual = counts.get(rule_id, 0)

            if actual > maximum:
                print(
                    f"     Rule regression: {rule_id}: "
                    f"{actual} > {maximum}"
                )
                failed = True

    print()
    print(
        f"Totals: {total_findings_all_packages} findings across corpus, "
        f"{total_high_confidence} high-confidence, "
        f"{total_guard_suppressed} suppressed by guard/shim detection."
    )
    print(
        "Note: the per-package 'rules' dicts in CORPUS above are "
        "regression ceilings (actual > recorded maximum fails the "
        "build), not exact expectations -- a count dropping below its "
        "recorded maximum is fine and expected as detection precision "
        "improves or an installed package version changes. See "
        "DELIVERY_NOTES.md, sections 35-39 and 79, for why exact-count "
        "goldens against a live pip-installed dependency are the wrong "
        "contract to enforce."
    )

    if failed:
        print()
        print(
            "[FAIL] Corpus benchmark failed -- "
            "precision regression detected."
        )
        return 1

    print()
    print("[OK] Corpus benchmark passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())