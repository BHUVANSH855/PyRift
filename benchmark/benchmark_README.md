# PyRift Benchmark Suite

This directory contains PyRift's quality verification pipeline.

## Files

```text
benchmark/
  run_benchmark.py   — Golden benchmark: 234 cases, 104/104 rules represented
  self_scan.py       — Self-scan gate: 121 files, 0 findings expected
  corpus.py          — Real project corpus benchmark
  runtime_harness.py — Runtime differential validation across Python versions
  expected.json      — Formal benchmark quality contracts for reviewed rules