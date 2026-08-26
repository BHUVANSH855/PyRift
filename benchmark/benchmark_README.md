# pyrift benchmark suite

This directory contains pyrift's quality verification pipeline.

## Files

```
benchmark/
run_benchmark.py — Golden benchmark: 122+ cases, 100% pass rate required
self_scan.py — Self-scan gate: pyrift scans its own source (0 findings expected)
corpus.py — Real project corpus: scans 7+ installed packages
runtime_harness.py — Runtime differential: verifies rules against CPython probe data
expected.json — False-positive budgets per rule
cpython_matrix.py — CPython version transition matrix documentation
```


## Running

``````bash
python benchmark/run_benchmark.py
python benchmark/self_scan.py
python benchmark/corpus.py
python benchmark/runtime_harness.py
``````

All four exit code 0 = quality gates pass.

## CI

All four run automatically on every push via .github/workflows/tests.yml
"@ -Encoding utf8
``````

Then commit:

```powershell
git add benchmark\benchmark_README.md
git commit -m "fix: repair CPY050 tests, expand benchmark to 122 cases/48% coverage, fix README/CHANGELOG test counts, archive stale report, strip 9 JSON BOMs, fix benchmark README"
git push origin main
```

Tell me when CI shows all green.