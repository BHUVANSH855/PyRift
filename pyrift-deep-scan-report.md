# PyRift — Deep Scan Report (Post-Fix Review #3)

**Project:** [BHUVANSH855/PyRift](https://github.com/BHUVANSH855/PyRift)
**Local path reviewed:** `C:\Users\milan\pyrift`
**Tool type:** Static-analysis linter that detects **silent Python behaviour differences** across CPython versions and across CPython vs PyPy.
**Commits reviewed:** latest `fb89ec4` — *"fix: strip BOM from 15 files, dedup import findings via by_statement(), utf-8-sig scanner, rename cpy050 typo, remove ppy043 orphan, ASCII-safe output, fix docs generator split, PPY009 false positive on id() as dict key, self-scan counts parse errors"*
**Date of scan:** 2026-08-26

> This is the **third** deep scan. The two prior scans flagged: UTF-8 BOM corruption (15 files), a systemic duplicate-finding bug, a blind self-scan gate, a Windows console-encoding crash, docs-count drift, and a broken docs auto-generator. This report verifies each fix end-to-end and identifies what remains.

---

## 1. Verdict Summary

| Metric | Value | Status |
|---|---|---|
| **Overall rating** | **8.1 / 10** | Trending up (was 7.2) |
| Active rules | **104** (58 CPython + 46 PyPy) | ✅ consistent |
| Tests | **495 passing** (3× consistent) | ✅ |
| Golden benchmark | **78 / 78 correct (100%)** | ✅ |
| Corpus benchmark | **Pass** | ✅ |
| Ruff | **All checks passed** | ✅ |
| Self-scan gate | **120 files, 0 parse errors, 0 errors** | ✅ fixed |
| Wheel build | **0 BOM files** (was 15) | ✅ fixed |
| BOM user-file scanning | Correctly detected (was false parse error) | ✅ fixed |
| Rule files vs registered | **104 = 104** | ✅ fixed |
| Rules documented in docs/rules.md | **104 / 104** | ✅ fixed |
| Docs generator split | **"58 + 46"** correct | ✅ fixed |
| Git working tree | Clean | ✅ |

---

## 2. What the Tool Is

- **Zero runtime dependencies** — pure `ast` static analysis.
- Flags **silent runtime behaviour differences**, which no other tool (ruff, pylint, mypy, pyright, pyupgrade, bandit, pip-audit) covers:
  - Cross-CPython-version drift (e.g. `tomllib` requires 3.11+, `distutils` removed in 3.12, `annotationlib` requires 3.14+).
  - CPython vs PyPy behaviour differences (e.g. `__del__` timing, `sys.getrefcount` meaninglessness, string concat O(n²)).
- Ships a clean Python API, a CLI, a baseline system, target-version awareness (`requires-python`), pre-commit hook, and GitHub Actions workflows.

---

## 3. Verification Battery Performed

Every check below was **actually executed** on the local repo:

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Full test suite (3 runs) | `python -m pytest tests/ -q` | 495 passed each time |
| 2 | Test collection count | `pytest --collect-only` | 495 tests |
| 3 | Lint | `python -m ruff check .` | All checks passed |
| 4 | Golden benchmark | `python benchmark/run_benchmark.py` | 78/78 (100%), `[OK]` |
| 5 | Self-scan gate | `python benchmark/self_scan.py` | 120 files, **0 parse errors**, 0 ERR, 11 WARN |
| 6 | Corpus benchmark | `python benchmark/corpus.py` | `[OK]` |
| 7 | CLI self-scan | `pyrift scan pyrift/` | **0 errors** (was 15 PARSE), 11 warnings |
| 8 | Unicode / Windows output | `pyrift scan ...` (no `PYTHONIOENCODING`) | `->` and `[OK]` — **no crash** |
| 9 | Wheel build + inspection | `python -m build --wheel` | **0 BOM files**, 120 py files, `analysis/` shipped |
| 10 | BOM'd user file scan | CLI on a UTF-8-BOM file | Correctly flagged `CPY004` (was false PARSE error) |
| 11 | Dedup probe | direct rule calls | `from tomllib import load, loads` → 1 CPY004; `from annotationlib import ...` → 1 CPY063 |
| 12 | Rule registry vs files | python | 104 rule files = 104 registered |
| 13 | Docs coverage | grep | 104/104 rules documented |
| 14 | Docs generator split | `python scripts/generate_docs.py` | "104 (58 CPython + 46 PyPy)" — correct |

---

## 4. Section-by-Section Ratings

| Section | Prev | Now | Basis |
|---|---|---|---|
| Concept / value | 9.0 | 9.0 | Unique niche, genuinely unserved |
| Architecture / code org | 8.0 | 8.5 | `by_statement()` dedup is a clean abstraction |
| Rule correctness | 6.0 | 7.5 | Dedup fixed; only PPY009 over-aggression remains |
| Testing | 8.0 | 8.5 | 495 solid tests; honest gate |
| Documentation | 7.0 | 7.5 | 104/104 docs; stale README counts + roadmap |
| Cross-platform | 4.5 | 7.5 | ASCII-safe output fixed |
| CI/CD | 7.0 | 8.5 | Self-scan gate is now real |
| Packaging | 6.5 | 8.5 | 0 BOMs in wheel, `analysis/` shipped |
| Hygiene | 7.5 | 8.5 | Clean tree, matching counts |
| DX / API | 8.5 | 8.5 | Clean public API, baseline, targets, pre-commit |

**Overall: 7.2 → 8.1 / 10**

---

## 5. Strengths (Verified)

1. **Genuinely useful niche.** No existing tool catches silent cross-version / CPython-vs-PyPy behaviour drift. Real value proposition.
2. **Clean architecture.** `BaseRule` ABC, registry in `scanner.py`, shared helpers in `pyrift/analysis/*` (`imports.py`, `calls.py`, `scope.py`), clean separation of `finding` / `reporter` / `fingerprint` / `baseline` / `targets`.
3. **Good false-positive reduction** in older rules:
   - `PPY014` requires static string evidence before flagging `+=` in loops.
   - `CPY001` deliberately skips set/frozenset dict-view comparisons.
   - `CPY051` tracks lock state through `with` / `try` / `finally` / `acquire`-`release`.
4. **Target-awareness (`targets.py`).** Parses `requires-python` (PEP-440 subset + pre-3.11 no-tomllib fallback) and filters findings outside the supported range.
5. **Baseline + fingerprinting.** Fingerprints exclude line numbers so code movement doesn't churn the baseline.
6. **Golden benchmark with confidence + evidence fields** (`benchmark/expected.json`, `run_benchmark.py`) — a real quality asset.
7. **Corpus benchmark** on real stdlib packages.
8. **104/104 rules documented** in `docs/rules.md`.
9. **Repo hygiene** — clean committed tree, `.gitignore` covers `*-scan.json`.

---

## 6. Fixes Verified From the Previous Review

### 6.1 UTF-8 BOM corruption — FIXED ✅
- `scanner.py:306` now reads `encoding="utf-8-sig"`.
- **0 BOM files** in source and **0 in the built wheel** (was 15).
- `pyrift scan pyrift/` → **0 PARSE errors** (was 15).
- A real-world BOM'd user file now **scans correctly** (detects `CPY004`) instead of returning a false `PARSE: Syntax error`.

### 6.2 Duplicate-finding bug — FIXED ✅
- `analysis/imports.py` gained `by_statement()` and a dedup `get()` (keyed on `id(import_node)`).
- Verified: `from tomllib import load, loads` → **1** CPY004; `from annotationlib import get_annotations, Format` → **1** CPY063 (both were 2).

### 6.3 Blind self-scan gate — FIXED ✅
- `benchmark/self_scan.py` now **counts and prints parse errors**, scans **120/120 files** (was silently skipping 15 → "106 files").
- Reports ASCII-safe `[OK]` / `[FAIL]`.

### 6.4 Windows console encoding crash — FIXED ✅
- Text reporter uses `->` (was `→`); scripts use `[OK]` (was `✅`). Verified no `UnicodeEncodeError` without `PYTHONIOENCODING`.

### 6.5 Orphan rule file — FIXED ✅
- `pyrift/rules/pypy/ppy043_slots_memory.py` removed. Rule files = registered = 104.

### 6.6 Docs generator split bug — FIXED ✅
- Now counts by ID prefix (or includes `both`), producing "58 CPython + 46 PyPy = 104" (was "58 + 44 = 102").

---

## 7. Remaining Issues

### 7.1 PPY009 false-positive fix is incomplete (now flags its own file) ⚠️
The rule now exempts `id()` used as a *direct subscript index*, but pyrift uses `id()` in other legitimate **transient** ways that get flagged:

- `pyrift/analysis/imports.py:66` — `node_id = id(i.node)` (local dedup set)
- `pyrift/analysis/imports.py:84` — `key = (id(i.node), ...)` (local dedup tuple)
- `pyrift/analysis/scope.py:19,26,32,39,43,52` — `parent_map.get(id(node))`, `id(child)`
- **`pyrift/rules/pypy/ppy009_id_stability.py:38,42` — the rule flags ITS OWN parent-map code.**

Result: self-scan shows **11 PPY009 warnings** (up from 9), including on its own rule file. The fix logic misses the most important case.

Secondary code smell: `ppy009_id_stability.py:39` checks `isinstance(parent, ast.Index)` — **`ast.Index` was removed in Python 3.9**, so that branch is dead code on Python 3.10+ (the tool's own minimum).

### 7.2 Committed README is stale (discovered during review) ⚠️
The committed `README.md` `## Project status` still shows:
```
- **Rules:** 104 (58 CPython + 44 PyPy)   ← wrong (sums to 102)
- **Tests:** 506 passing                  ← wrong (actual 495)
```
The user fixed `scripts/generate_docs.py` and the test suite, but **did not re-run the generator**, so the committed README was left stale. Running the generator produces the correct **"58 + 46 / 495"** (verified), then I reverted to keep the user's tree clean.

### 7.3 README roadmap lists already-taken rule IDs ⚠️
`README.md:188-189` still lists `CPY046` (TypeIs) and `CPY047` (ReadOnly) as **planned**, but both IDs are **already shipped**:
- `CPY046` = "open() without encoding= uses platform-dependent encoding before 3.15"
- `CPY047` = "collections.abc.ByteString removed in Python 3.15"

Contributors reading the roadmap will try to claim dead IDs.

### 7.4 Minor self-scan comment drift
`benchmark/self_scan.py:25` comment says "PPY009 (9x)" but the actual count is now **11x**.

---

## 8. What Improved (Credit)

- ✅ Each fix from the prior two scans was independently verified working.
- ✅ The migration to shared `analysis` utilities is complete and the dedup abstraction (`by_statement()` / `get()`) is well-designed.
- ✅ CI now enforces an *honest* self-scan gate.
- ✅ Wheel ships clean, BOM-free code.
- ✅ Full 104-rule documentation.

---

## 9. Remaining Priority Fix List

| # | Item | Effort | Impact |
|---|---|---|---|
| 1 | **PPY009**: exempt transient `id()` keys (dedup sets/tuples, parent-map building) and **stop the rule flagging its own file**; drop the dead `ast.Index` branch | Medium | Clean self-scan (11→0 warnings) |
| 2 | **Re-run `scripts/generate_docs.py` and commit README** so committed stats read "58 + 46 / 495" | Small | Correct docs |
| 3 | **Update README roadmap** — remove taken `CPY046/047`, list truly-free IDs | Small | Contributor clarity |
| 4 | **Fix `self_scan.py` stale "9x" comment** → 11 | Trivial | Accuracy |

No other correctness, cross-platform, or packaging blockers remain. With the four items above, this would be a very clean ~8.5/10.

---

## 10. Detailed Rule-Accuracy Notes (Sampled, Verified)

- `CPY007` removed-modules set (PEP 594) — 21 modules, matches spec. ✅
- `CPY038` `asyncio.get_event_loop()` — flagged as error on 3.14+; defensible. ✅
- `CPY063` `annotationlib` requires 3.14+ (PEP 749) — correct, now deduplicated. ✅
- `CPY051` free-threading — honest heuristic, WARNING severity appropriate. ✅
- `CPY046` "open() without encoding" (platform-dependent before 3.15) — non-obvious, high-value rule. ✅
- PyPy rules generally accurate; several are performance-not-correctness issues, severity reflects that. ✅

---

## 11. Artifacts Observed

| Artifact | Status |
|---|---|
| `cython-3.10-scan.json`, `cython-3.12-scan.json`, `cython-main-scan.json`, `pypy-libpypy-scan.json` | Gitignored lefto-overs |
| `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache` | Ignored |

---

*Report generated by structural review plus direct execution of the test suite, benchmarks (golden + corpus), lint, CLI self-scan, wheel build + archive inspection, and live BOM-file scanning in the local repo.*