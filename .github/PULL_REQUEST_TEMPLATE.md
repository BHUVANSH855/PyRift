## Summary

What does this change do and why?

## Compatibility evidence

Which Python / runtime versions are affected (if a rule change)?

## Tests

List the tests and benchmarks that were run:

- [ ] `python -m pytest tests/ -q`
- [ ] `python benchmark/run_benchmark.py`
- [ ] `python benchmark/self_scan.py`
- [ ] `python benchmark/corpus.py` (if rule detection changed)
- [ ] `python benchmark/runtime_harness.py` (if runtime evidence changed)
- [ ] `python scripts/generate_docs.py` + `python scripts/check_docs.py`
- [ ] `python -m ruff check .`
- [ ] `git diff --check`

## Documentation

What documentation was updated?

- [ ] `docs/rules.md`
- [ ] `README.md`
- [ ] `CHANGELOG.md`

## Behaviour changes

Did existing findings, benchmark contracts, or CLI behaviour change? If so,
why?

## Related issue

Closes #_ (if applicable).

---
By submitting this PR, you confirm your changes follow the
[Contributor Covenant](CONTRIBUTING.md#code-of-conduct) and the
validation standard described in `CONTRIBUTING.md`.