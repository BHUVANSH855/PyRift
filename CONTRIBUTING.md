# Contributing to PyRift

Thank you for contributing to **PyRift** — a static-analysis scanner that detects **silent Python behaviour differences** across CPython versions and between CPython and PyPy.

The most valuable contributions fix **real compatibility problems**: verified runtime behaviour, a minimal reproduction, a precise AST pattern, and regression tests. Correctness and evidence matter more than finding count.

> Current baseline: `0.8.0` · 706 tests · 104 rules · ~97% coverage. If a section conflicts with the tree, the code is the source of truth — open an issue.

---

## Ways to contribute

- Add / improve rules · reduce false positives · improve diagnostics
- Add regression & edge-case tests
- Improve Git/`--changed-only` scanning · CLI · benchmarks · docs · CI
- Fix bugs

---

## Setup

```bash
git clone https://github.com/BHUVANSH855/PyRift.git
cd PyRift
python -m pip install -e ".[dev]"
pyrift --help
```

---

## Repository layout

```text
pyrift/
├── analysis/       calls.py, imports.py, scope.py   (shared AST helpers)
├── rules/cpython/  CPY001..CPY063   (version compatibility)
├── rules/pypy/     PPY001..PPY047   (CPython vs PyPy)
├── base_rule.py, finding.py, scanner.py, targets.py
├── rule_metadata.py  (authoritative confidence/evidence)
├── baseline.py, fingerprint.py, git.py, reporter.py, cli.py

tests/  test_*.py + cpython/ and pypy/ (one test module per rule)
benchmark/  run_benchmark.py, expected.json, self_scan.py, corpus.py, runtime_harness.py
compatibility-benchmark/   (historical runtime probe data)
scripts/  generate_docs.py, check_docs.py
docs/rules.md  (auto-generated, 104/104)
```

Follow the style of the code already present. Update tests + docs alongside any behaviour change.

---

## Finding metadata

Each rule returns `Finding` objects with `severity` (`ERROR`/`WARNING`/`INFO`), `runtime` (`CPYTHON`/`PYPY`/`BOTH`), `affected_from`/`affected_until`, `confidence`, and `evidence`.

**You don't set `confidence`/`evidence` by hand.** Authoritative values live in `pyrift/rule_metadata.py` and are attached automatically via `Finding.__post_init__`.

**Conservation rule:** an unreviewed rule (no `RULE_METADATA` entry) stays at `LOW`/`INFERRED` — it must never claim high confidence silently.

---

## Adding a rule

1. **Pick the next free ID** — `CPY064+` or `PPY048+`; never reuse an ID.
2. **Create** `pyrift/rules/cpython/cpyXXX_name.py` or `pyrift/rules/pypy/ppyXXX_name.py`, subclassing `BaseRule`:

   ```python
   class YourRuleName(BaseRule):
       rule_id = "CPYXXX"
       title = "Short title"
       runtime = "cpython"

       def check(self, node, filename):
           findings = []
           for n in ast.walk(node):
               if isinstance(n, ast.SomeNode):
                   findings.append(Finding(
                       file=filename, line=n.lineno, col=n.col_offset,
                       rule_id=self.rule_id, title=self.title,
                       description="Why this is a problem.",
                       severity=Severity.WARNING, runtime=Runtime.CPYTHON,
                       affected_from="3.x", affected_until="3.y",
                       suggestion="Concrete fix.",
                       docs_url="https://docs.python.org/...",
                   ))
           return findings
   ```

   Prefer the `pyrift.analysis` helpers (e.g. `collect_imports().by_statement()`/`get()`) so multi-name `from x import a, b` reports **one** finding per statement, not per name.

3. **Keep it conservative.** Prefer a narrow, confident AST pattern over a broad heuristic that produces false positives.
4. **Register it** in `pyrift/scanner.py` (`ALL_RULES`), then:

   ```bash
   python -m pytest tests/test_rule_inventory.py -q
   ```

5. **Add tests** in `tests/cpython/` or `tests/pypy/` (one module per rule). Use the local helper convention:

   ```python
   def parse(src): return ast.parse(textwrap.dedent(src))
   def run(rule, src): return rule.check(parse(src), "<test>")
   ```

   Provide positive + negative + edge cases (aliases, nested forms, multi-finding).
6. **Add a benchmark contract** in `benchmark/run_benchmark.py` + `benchmark/expected.json`:

   ```bash
   python benchmark/run_benchmark.py   # must stay 104/104, 100% correct
   ```

   Don't weaken existing contracts to make a rule pass.
7. **Update metadata** in `pyrift/rule_metadata.py` — be honest:

   ```python
   "CPYXXX": _metadata("high", "pep:XXXX")   # or "runtime_probe", "official_docs", "observed", "inferred"
   ```
8. **Verify runtime claims** where practical:

   ```bash
   python benchmark/runtime_harness.py
   ```

   Don't claim a runtime difference from memory.
9. **Document the rule** in `docs/rules.md` (what, why, versions, example, fix, official link).

---

## Modifying a rule / fixing false positives

Read the implementation, its tests, benchmark contract, metadata, and docs first. Then:

1. Reproduce the issue with the smallest example.
2. Add a **regression test** (fails before, passes after).
3. Narrow the AST/context analysis — no hacky filename/project exceptions.
4. Confirm existing positive cases still fire.
5. Run the self-scan — the project must stay clean:

   ```bash
   python benchmark/self_scan.py   # currently 0 findings
   ```

Don't suppress findings blindly.

---

## Git / `--changed-only`

Changes live in `pyrift/git.py` (tests: `test_git.py`, `test_changed_only_e2e.py`, `test_cli_baseline.py`). Handle staged + untracked + renamed/deleted files, Unicode/whitespace paths, invalid revisions, and failing cleanly outside a repo.

```bash
python -m pytest tests/test_git.py tests/test_changed_only_e2e.py tests/test_cli_baseline.py -q
pyrift scan . --changed-only
pyrift scan . --changed-only --base origin/main
```

---

## Documentation & generated statistics

PyRift keeps its project statistics in sync **automatically** — CI fails if they drift:

```bash
python scripts/generate_docs.py    # regenerate README/CHANGELOG counts + rules.md
python scripts/check_docs.py       # gate: committed docs must match live pytest count
```

Run both after any rule/test change. Never hand-edit generated statistics.

---

## Validation before a PR

```bash
python -m ruff check .
python -m pytest tests/ --tb=no -q
git diff --check
python scripts/generate_docs.py && python scripts/check_docs.py
python benchmark/run_benchmark.py   # golden, 104/104
python benchmark/self_scan.py       # 0 findings on the project itself
python benchmark/corpus.py          # real-package corpus
python benchmark/runtime_harness.py # runtime probes
```

All applicable checks must pass before opening a PR.

---

## Testing philosophy

Tests define the compatibility contract. They must be deterministic and network-free. Prefer mocking the `git` subprocess for parsing/error-handling tests; use end-to-end tests for real repo behaviour.

---

## Code quality & commits

- `python -m ruff check .` and `git diff --check` must both pass.
- Prefer clear, maintainable Python; keep functions focused.
- Use concise commit messages: `feat:`, `fix:`, `test:`, `docs:`, `chore:`.

---

## Pull requests & bugs

**PR description:** summary · compatibility evidence (versions affected) · tests run · docs updated · behaviour changes · related issue.

**Bug report:** version, Python, OS, command, minimal example, actual vs expected output, full vs `--changed-only` mode, traceback.

---

## Rule quality bar (checklist)

A new/substantially modified rule must:

- [ ] Detect a real runtime compatibility difference
- [ ] Have correct affected-version range, severity, runtime
- [ ] Have an actionable suggestion + official docs link
- [ ] Have positive, negative, and edge-case tests
- [ ] Have a benchmark contract
- [ ] Be registered in `pyrift/scanner.py` (inventory test passes)
- [ ] Have honest metadata in `pyrift/rule_metadata.py`
- [ ] Be documented in `docs/rules.md`
- [ ] Pass self-scan + golden benchmark (no unjustified false positives)

---

## Maintainer review checklist

```text
[ ] Solves a real compatibility problem        [ ] No duplicated rule/functionality
[ ] Tests + regression tests cover the change  [ ] Benchmark contracts updated
[ ] Rule metadata is honest and correct        [ ] generate_docs.py + check_docs.py pass
[ ] Ruff passes     [ ] pytest passes     [ ] git diff --check passes
[ ] Golden benchmark passes  [ ] Self-scan passes  [ ] Corpus passes
[ ] Runtime harness passes (where relevant)    [ ] Changed-only passes (where relevant)
[ ] No debug/temp files; diff is intentional
```

---

## Code of conduct

PyRift follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful, constructive, and specific — focus on the code and the problem, not the person.

Thank you for helping make PyRift a reliable compatibility tool for Python developers and maintainers.