# PyRift Benchmark Suite

This directory contains PyRift's quality verification pipeline.

## Files

```text
benchmark/
  run_benchmark.py   — Golden benchmark: 154 cases, 66 rules represented
  self_scan.py       — Self-scan gate: 122 files, 0 findings expected
  corpus.py          — Real project corpus benchmark
  runtime_harness.py — Runtime differential validation across Python versions
  expected.json      — Formal benchmark quality contracts (78 rules)
```

## Historical Note

Older benchmark reports (e.g. the 231-case count referenced in prior
documentation) are from earlier versions of the benchmark suite. The
current suite uses the numbers above. Historical scan reports are
archived in `docs/archive/`.
