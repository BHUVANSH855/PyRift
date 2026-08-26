# pyrift benchmark suite

This directory contains pyrift's quality verification pipeline.

## Files

```
benchmark/
  run_benchmark.py   — Golden benchmark: 134 cases, 54/104 rules, 100% pass required
  self_scan.py       — Self-scan gate: 121 files, 0 findings expected
  corpus.py          — Real project corpus: 7 installed packages
  runtime_harness.py — Runtime differential: 5 rules × 6 Python versions
  expected.json      — False-positive budgets per rule
  cpython_matrix.py  — CPython version transition matrix
```

## Running

```bash
python benchmark/run_benchmark.py    # 134 cases, 54/104 rules (51.9%)
python benchmark/self_scan.py        # self-scan, 0 findings expected
python benchmark/corpus.py           # 7 real packages
python benchmark/runtime_harness.py  # runtime differential (needs probe files)
```

All four exit code 0 = quality gates pass.

## CI

All four run automatically on every push via `.github/workflows/tests.yml`.

The runtime harness runs with `continue-on-error: true` since probe files
are gitignored — generate them locally with:

```bash
python compatibility-benchmark/cpython_runtime_probe.py
```

## Coverage goal

Current: 54/104 rules (51.9%)
Target:  80+/104 rules

Add benchmark cases in `run_benchmark.py` under the `GOLDEN` dict —
at least one positive and one negative case per rule.