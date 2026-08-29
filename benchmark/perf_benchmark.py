#!/usr/bin/env python3
"""
Performance benchmark for pyrift.

Measures scan time, throughput, and optionally memory usage
over multiple iterations. Uses only stdlib — no extra dependencies.

Run:
    python benchmark/perf_benchmark.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pyrift.scanner import scan

ITERATIONS = 3
SRC_DIR = Path(__file__).parent.parent / "pyrift"

try:
    import tracemalloc

    HAS_TRACEMALLOC = True
except ImportError:
    HAS_TRACEMALLOC = False


def _count_py_files(root: Path) -> int:
    count = 0
    for _, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                count += 1
    return count


def _run_one_iteration() -> dict:
    start = time.perf_counter()
    result = scan(SRC_DIR, use_project_config=False)
    elapsed = time.perf_counter() - start

    return {
        "time": elapsed,
        "files": result.files_scanned,
        "findings": len(result.findings),
    }


def main() -> None:
    total_files = _count_py_files(SRC_DIR)
    print("PyRift Performance Benchmark")
    print(f"Target: {SRC_DIR}")
    print(f"Python files in target: {total_files}")
    print(f"Iterations: {ITERATIONS}")
    print()

    peak_memory_mb: float | None = None

    if HAS_TRACEMALLOC:
        tracemalloc.start()

    times: list[float] = []
    files_list: list[int] = []
    findings_list: list[int] = []

    for i in range(ITERATIONS):
        stats = _run_one_iteration()
        times.append(stats["time"])
        files_list.append(stats["files"])
        findings_list.append(stats["findings"])
        print(
            f"  Iter {i + 1}: {stats['time']:.3f}s, "
            f"{stats['files']} files, "
            f"{stats['findings']} findings"
        )

    if HAS_TRACEMALLOC:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = peak / (1024 * 1024)

    print()
    min_time = min(times)
    max_time = max(times)
    avg_time = sum(times) / len(times)

    min_files = min(files_list)
    max_files = max(files_list)
    avg_files = sum(files_list) / len(files_list)

    min_findings = min(findings_list)
    max_findings = max(findings_list)
    avg_findings = sum(findings_list) / len(findings_list)

    files_per_sec = avg_files / avg_time if avg_time > 0 else 0
    findings_per_sec = avg_findings / avg_time if avg_time > 0 else 0

    print("=" * 60)
    print(f"{'Metric':<25} {'Min':>10} {'Avg':>10} {'Max':>10}")
    print("-" * 60)
    print(f"{'Scan time (s)':<25} {min_time:>10.3f} {avg_time:>10.3f} {max_time:>10.3f}")
    print(f"{'Files scanned':<25} {min_files:>10} {avg_files:>10.0f} {max_files:>10}")
    print(f"{'Findings':<25} {min_findings:>10} {avg_findings:>10.0f} {max_findings:>10}")
    print("-" * 60)
    print(f"{'Files/sec':<25} {'':>10} {files_per_sec:>10.1f} {'':>10}")
    print(f"{'Findings/sec':<25} {'':>10} {findings_per_sec:>10.1f} {'':>10}")

    if peak_memory_mb is not None:
        print(f"{'Peak memory (MB)':<25} {'':>10} {peak_memory_mb:>10.2f} {'':>10}")
    else:
        print(f"{'Peak memory (MB)':<25} {'':>10} {'N/A':>10} {'':>10}")

    print("=" * 60)


if __name__ == "__main__":
    main()
