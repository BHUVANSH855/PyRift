# pyrift benchmark suite

This directory contains the golden benchmark fixtures for pyrift.

## Structure

```
benchmark/
  fixtures/        — Python source fixtures (positive + negative cases)
  expected/        — Expected finding counts per rule
  run_benchmark.py — Benchmark runner (fails CI on regression)
```

## Running

```bash
python benchmark/run_benchmark.py
```

Exit code 0 = all rules within expected bounds.
Exit code 1 = precision regression detected.