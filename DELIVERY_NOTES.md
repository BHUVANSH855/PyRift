# DELIVERY_NOTES — response to the 2026-09 architecture review

This file exists so nothing in the review gets silently dropped. Every
numbered point from the review is listed below as one of:

- **DONE** — implemented and covered by a passing automated test in
  this codebase (run `pytest tests/`, `python benchmark/run_benchmark.py`,
  `python benchmark/runtime_harness.py`, `python benchmark/self_scan.py`
  to verify yourself).
- **PARTIAL** — a real, working piece of the ask is implemented; the
  rest is scoped out below.
- **DEFERRED** — not attempted in this pass, with a one-line reason.
  Deferred does not mean rejected — it means "this is a multi-week
  effort on its own and doing it hastily would produce something worse
  than not doing it" (real-world corpora, mutation testing, an
  automated PEP-ingestion pipeline, etc.), or "lower priority than the
  P0 items given limited time."

Overall: this pass focused entirely on the review's own **P0** list
(section 97), because that's what the review itself says must happen
before anything else is worth doing. P1/P2 (sections 98-99) are
untouched except where a P0 fix happened to also satisfy one.

## Headline numbers after this pass

- 1,330 tests passing (up from 1,299; +31 new tests for the changes
  below), 0 failing.
- Golden benchmark: 270/270 cases correct (was 268/268 — the CPY023
  narrowing added 2 new cases), 118/118 rules covered.
- Self-scan: 143 files, 0 findings, 0 rule errors — unchanged.
- Runtime harness: now exits non-zero when it has no evidence, instead
  of claiming success.

## Section-by-section status

### 1-2. Executive verdict / taxonomy problem — **DONE**
`RuleCategory` (SEMANTIC / COMPATIBILITY / IMPLEMENTATION / PERFORMANCE)
added to `pyrift/finding.py` and wired through `Finding.category` via
`pyrift/rule_metadata.py`. All 118 rules now carry a category based on
the review's own bucket-A/B/C examples (CPython) and Tier-A/B/C
examples (PyPy), generalized by a documented, conservative heuristic
for the rules the review didn't classify individually (see
`_default_cpy_category` / `_default_pypy_category` in
`rule_metadata.py`). `scanner.py` no longer blanket-overwrites every
finding's category to `"compatibility"` — that was an actual bug, not
just an architectural gap: `RULE_METADATA`'s classification was always
being discarded before this fix.

CLI-level `PYRIFT-SEMANTIC` / `PYRIFT-COMPAT` / etc. prefixes (as
literally proposed in section 3) were **not** added — that's a
cosmetic, rule-ID-renaming change that would break every existing
integration/baseline keyed on rule IDs for no functional benefit over
the `category` field, which already gives callers the same
information. Flagging this as a deliberate deviation, not an omission.

### 4. Evidence system / claim schema — **PARTIAL**
Full per-rule YAML claim schema (section 4's worked example) was not
built — that's a large, separate data-modeling project. What's real:
`ContractStatus` enum (GUARANTEED/DOCUMENTED/IMPLEMENTATION_DEFINED/
DEPRECATED/REMOVED/OBSERVED/UNKNOWN) added and populated for every
rule; multidimensional confidence (`claim_confidence`,
`detection_confidence`, with the invariant that overall `confidence`
can never exceed the weaker of the two — enforced in
`Finding.__post_init__` and checked by `rule_metadata.validate_metadata()`).

### 5-6. Runtime harness honesty / reproducible evidence — **DONE** (5), **DEFERRED** (6)
`benchmark/runtime_harness.py` rewritten:
- Reports `VERIFIED` / `PARTIALLY_VERIFIED` / `FAIL` per rule instead of
  a blanket `[SKIP]` that still counted as overall success.
- The final summary now always states *how many of the 118 rules were
  actually checked* (currently 7) instead of claiming "All rules
  verified against runtime probe data."
- Exits non-zero when no probe data exists at all, instead of printing
  `[OK] Harness skipped` and returning 0.
- Cross-checked against a new `FULLY_RUNTIME_VERIFIED_RULES` constant
  in `rule_metadata.py`, which is the *only* way a rule's
  `runtime_verification` field may be `VERIFIED`; every other rule is
  `NOT_APPLICABLE` (not silently blank). `tests/test_runtime_harness_honesty.py`
  enforces this stays true, including a monkeypatched test that the
  harness now correctly fails closed with no probe data.

Section 6's `evidence/cpython/<RULE>/<version>.json` directory
restructuring is **DEFERRED** — the existing flat
`compatibility-benchmark/runtime-<version>.json` files aren't wrong,
just less granular; re-organizing them is a mechanical follow-up once
more rules have real probes, not a correctness fix.

### 7. CPY023 evidence problem — **DONE**
Rewrote `cpy023_multiprocessing_fork.py`: a bare `import multiprocessing`
no longer triggers a finding. The rule now requires an actual
`Process(...)`, `Pool(...)`, or argument-less `get_context()` call.
Confidence downgraded from HIGH to MEDIUM to reflect that even this is
still a proxy signal, not proof of fork-reliance (per the review's own
framing in this section). Existing tests that encoded the old
false-positive-prone behavior as "expected" were rewritten, not just
patched — `test_import_multiprocessing_alone_triggers` became
`test_import_multiprocessing_alone_does_not_trigger`.

### 8. CPY051 free-threading target model — **PARTIAL**
Confidence downgraded to MEDIUM with `claim_confidence=medium` and an
explanatory comment in `rule_metadata.py` acknowledging free-threading
is a build configuration, not a version range. The full
`TargetConfig.free_threading` tri-state field, CLI flag, and
`pyproject.toml` key described in the review are **DEFERRED** — this
needs a decision on the actual config surface (CLI flag vs.
`pyproject.toml` key vs. both) that's a product decision, not something
to guess at silently.

### 9. CPY057 consumer-version awareness — **DEFERRED**
Not implemented. Would need a `--consumer-python` / `pyproject.toml`
config surface plus wiring into the rule; same reasoning as point 8 —
this is a real, scoped feature, not a quick fix, and deserves its own
review rather than being bolted on here.

### 10. CPY046 intent modeling — **DEFERRED**
Genuinely requires the data-flow/semantic layer from sections 13-14,
which is out of scope for this pass (see below).

### 11. CPY001 dict/set comparison precision — **NOT RE-VERIFIED**
The review notes this was already fixed and closed on your tracker
before this pass; not re-touched here.

### 12-13. Shared AST index / semantic layer — **DEFERRED**
This is the single largest ask in the whole review (a full
name/scope/import-resolution layer) and rewriting how all 118 rules
consume the AST is exactly the kind of high-risk, high-effort change
that needs its own dedicated project with a much larger regression
safety net than "1,330 tests still pass." Attempting a partial version
here would leave the codebase in a worse, half-migrated state.

### 14. Import alias resolution — **ALREADY PARTIALLY PRESENT, NOT EXTENDED**
`pyrift/analysis/imports.py` already tracks `alias`/`name`/`module` per
import and has version-guard detection for the `>=`/`>` case. This pass
extended the *version-guard* half of that file's job into a general,
rule-agnostic module (`pyrift/analysis/guards.py`, see points 73-78
below) rather than duplicating alias-resolution logic per rule.
Rule-by-rule adoption of full alias-invariance (`pickle` vs `import
pickle as p` vs `from pickle import dumps`) for every one of 118 rules
is **DEFERRED** — `collect_imports()` already supports this for rules
that use it; not every rule does yet.

### 15. Scope sensitivity for PyPy rules — **DEFERRED**
Needs the semantic layer from 12-13.

### 16-17. PyPy evidence taxonomy / tiering — **DONE**
`RuleTier` (TIER_A/TIER_B/TIER_C/NOT_TIERED) added and populated using
the review's own explicit lists in section 47:
- **TIER_A** (17 rules, kept at HIGH confidence): PPY001, 003, 004, 009,
  013, 014, 016, 017, 019, 025, 026, 028, 029, 031, 032, 034, 045.
- **TIER_B** (4 rules, downgraded to MEDIUM, `category=PERFORMANCE`):
  PPY027, 038, 042, 049.
- **TIER_C** (16 rules, downgraded to MEDIUM where they were
  previously HIGH): PPY002, 005, 018, 021, 030, 035, 036, 037, 039,
  040, 041, 044, 047, 051, 052, 053.
- Everything else PyPy-side (PPY006, 007, 008, 010, 011, 012, 015, 022,
  023, 024, 033) is `NOT_TIERED` — i.e. explicitly flagged as "not yet
  reviewed against this rubric," rather than silently assumed Tier A.
  This is intentional: I was not going to invent tier judgments for
  rules the review didn't examine.

### 18. PPY035 C-extension over-broadness — **PARTIAL**
Confidence downgraded to MEDIUM with an explanatory comment. The
narrower detector (distinguishing "imports a C extension" from "uses a
CPython-only implementation detail") described in the review is
**DEFERRED** — it needs a maintained list of which packages/APIs
actually rely on CPython internals, which is a research task, not a
quick fix.

### 19-21. PPY014/016/019 precision — **NOT RE-VERIFIED**
Not independently re-audited against the review's suggested stronger
patterns (`next(iter(...))`, `float('nan') is float('nan')` vs generic
`is`, etc.) in this pass — flagging as open for a future audit rather
than claiming they were checked.

### 22-23. CPY031/CPY032 evidence correction — **DONE**
Both rules previously cited the wrong PEP (PEP 673 = `Self`, not
`assert_never`; PEP 544 = Protocols, not `reveal_type`). Fixed in three
places: `rule_metadata.py` (`evidence_source` now `official_docs`), the
rule files themselves (corrected docstrings and `docs_url` now points
at the typing module docs instead of the wrong PEP), and
`benchmark/expected.json` (the golden-benchmark contract that would
otherwise have kept asserting the wrong evidence forever).

### 24. Multidimensional confidence — **DONE**
See section 4 above.

### 25-26. Intent model / contract_status — **DONE**
`ContractStatus` enum added and populated per-rule as described in
section 26's exact proposal.

### 27. Platform scope on every semantic claim — **PARTIAL**
Added a `platform_scope` field to `Finding` and `rule_metadata`, and
used it for CPY023 (`"posix_non_macos"`). Not yet populated for every
other platform-sensitive rule (`CPY046`, `PPY002`, etc.) — that's a
per-rule audit, not a schema problem, and the schema is now in place
for it to be filled in incrementally.

### 28. TargetConfig compatibility model — **DEFERRED**
See points 8-9. The full `implementations` / `platforms` /
`free_threading` / `consumer_versions` dataclass redesign is a breaking
change to a public API (`pyrift.targets.TargetConfig`) that deserves
its own PR and version bump, not a silent expansion bundled into a
larger patch.

### 29. Version parser honesty — **NOT ADDRESSED**
Still describes itself accurately as a minor-version-constraint parser
in its own module; the review's ask was mostly "don't imply broader
PEP 440 support than you have," and a `grep` of the codebase shows it
already doesn't claim that. No change made.

### 30-32. Target-aware parsing / phase field — **DEFERRED**
Parsing with a version-appropriate grammar is a substantial feature
(effectively vendoring or shelling out to multiple Python grammars).
The `phase` diagnostic field (parse/import/call/runtime/semantic/
performance) is a reasonable, smaller addition that didn't make it into
this pass purely on time; it's a natural follow-up now that
`RuleCategory` exists.

### 33-34. Rule failure visibility / SARIF notifications — **NOT ADDRESSED**
`rule_errors` already exists and CLI already exits non-zero on it
(pre-existing, not this pass). Dedicated `ANALYZER001` diagnostics and
SARIF `toolExecutionNotifications` are **DEFERRED**.

### 35-39. Golden tests vs. ground truth / mutation testing / corpora — **DEFERRED**
This is explicitly the review's own "don't do this next" list until the
P0 foundation is solid (section 57) — treated it the same way here.
No mutation-testing harness, no `tests/corpus/{true_positive,
true_negative,ambiguous}` restructuring, no "ambiguous" finding
category added. These are real, good ideas; they're P1/P2 by the
review's own ordering.

### 40-41. Rule lifecycle / last_verified meaning — **PARTIAL**
`rule_tier` (PyPy) doubles as a lightweight lifecycle signal
(`NOT_TIERED` = "not yet reviewed"). `last_verified` dates for CPY031/
CPY032 were bumped to reflect the actual date they were re-verified in
this pass (2026-09-13); every other rule's date is untouched since it
wasn't actually re-checked, which is the honest thing to do rather than
bulk-updating dates without doing the work.

### 42-44. Automated PEP/What's-New ingestion — **DEFERRED**
Genuinely a multi-week research/tooling project on its own; not
attempted.

### 45-53. Rule-file size / data-driven rules / codebase consolidation — **DEFERRED**
No rule files were restructured into a declarative format. This is a
large refactor best done deliberately, rule-family by rule-family, with
its own review — not as a side effect of a metadata/taxonomy pass.

### 54. README ambition — **DEFERRED**
Not edited in this pass (time). Flagging explicitly: the README's
"Detect silent Python behaviour differences" framing should be softened
per the review's suggested wording once the taxonomy work above is
merged and can be described accurately.

### 55-56. Ecosystem positioning — informational, no action needed.

### 57-60. Don't add more rules / findings format — **DONE (in spirit)**, **NOT ADDRESSED (format)**
No new rules were added in this pass, consistent with the review's own
recommendation. The rich multi-field finding format mocked up in
section 60 is **not** implemented as a CLI text renderer in this pass,
but every field it references (`contract_status`, `claim`/`detection`
confidence, etc.) now exists on `Finding` and is available to build
that renderer from.

### 61-62. Context-sensitive confidence / suppression reasons — **PARTIAL**
`Finding.context_note` added and populated by the new guard-suppression
pass (see 73-78) for the one case that downgrades rather than drops a
finding (`TYPE_CHECKING` blocks). A general `# pyrift: ignore RULE --
reason` inline-suppression-with-required-reason comment syntax was
scoped but not implemented in this pass — flagging as the natural next
increment on top of the guard system.

### 63. Baseline expiry / reason — **DEFERRED**
Not implemented; existing baseline format (`fingerprint -> suppressed`)
is unchanged.

### 64-67. Determinism / scalability / fuzz-harness improvements — **NOT ADDRESSED**
No changes to `test_deterministic.py`, `perf_benchmark.py`, or
`fuzz_harness.py` in this pass.

### 68-72. Alias/shadowing/scope test coverage — **NOT ADDRESSED**
No new tests for import-alias invariance, builtin shadowing, or
attribute shadowing were added. This needs the semantic layer (12-13)
to fix properly rather than adding tests for behavior that doesn't
exist yet.

### 73-78. Version guards / implementation guards / compatibility shims — **DONE**
This was the other major implementation in this pass, alongside the
taxonomy work. New module `pyrift/analysis/guards.py` builds a
per-file `GuardIndex` covering:
- `sys.version_info` comparisons (`>=`, `>`, `<`, `<=`), including the
  `else` branch of each.
- `sys.implementation.name == "pypy"` / `platform.python_implementation()
  == "PyPy"` (and their `!=` negations), including `else` branches.
- `if TYPE_CHECKING:` blocks.
- `try/except ImportError` (and `ModuleNotFoundError`, and bare
  `except:`) compatibility shims, covering both the `try` and `except`
  bodies.

Wired into `scanner.py` as a **generic, rule-agnostic post-filter**
(`_apply_guards`) rather than threading a context object through all
118 `check()` methods — deliberately the lower-risk implementation path
given the size of the existing rule catalog. A version/implementation-
guarded or shimmed **compatibility**-category finding is suppressed
outright; a `TYPE_CHECKING`-only finding is downgraded (confidence LOW,
severity INFO, `context_note` explaining why) rather than dropped,
since it can still matter to someone running a type checker on an old
interpreter; **semantic**-category findings (genuine silent behavior
differences) are never suppressed by an import shim, since a shim only
neutralises an ImportError risk, not an actual behavior change.
`ScanResult.guard_suppressed` reports how many findings this filter
removed, mirroring the existing `baseline_suppressed` pattern. Covered
by `tests/test_guards.py` (19 tests) including 4 end-to-end
scanner-integration tests.

### 79-82. Real-world package corpus / CPython self-scan — **PARTIAL (2026-09-14 update)**
`benchmark/corpus.py` had a latent correctness bug independent of this
review: `scan_package()` called `rule.check()` directly in a hand-rolled
loop, bypassing `scanner.py` entirely -- which meant the guard/shim
suppression pass from points 73-78 (above) was never exercised by the
one benchmark that's supposed to validate precision on real code.
Fixed: `scan_package()` now calls `pyrift.scan()`, the same entry point
the CLI uses, and reports `guard_suppressed` and a confidence breakdown
per package.

Extended the corpus with three more packages from the review's own
suggested list (`packaging`, `click`, `pydantic`), chosen because they
actually exercise the guard/shim suppression on real code: scanning
`packaging` 26.0 and `pydantic` 2.13.5 as installed from PyPI on
2026-09-14 shows 2 and 6 findings respectively suppressed by version-
guard/shim detection that a pre-guards version of pyrift would have
reported as false positives.

Also produced one piece of real-world evidence for the review's own
point 18 (PPY035 too broad): scanning `pydantic` 2.13.5 with
`runtime=Runtime.BOTH` (i.e. not filtered to CPython-only) surfaces 44
separate PPY035 findings -- essentially one per call site touching
pydantic-core. That's a directly measured number, not an estimate, and
it's documented inline in `benchmark/corpus.py` as supporting evidence
for narrowing that detector (still tracked as future work, not fixed
in this pass -- see point 18 above).

Also corrected: the corpus's per-rule `"rules"` ceiling dicts *are*
actually enforced (a per-rule count exceeding its recorded maximum
fails the build) -- an earlier pass at this file briefly mischaracterized
them as dead/unused code before checking the `main()` loop closely
enough. They're accurately described as regression ceilings, not exact
expectations, in the module's own output now.

Still not done: a broader run across the review's full suggested list
(urllib3, Django, NumPy, SciPy, pandas, pytest, cryptography, FastAPI,
SQLAlchemy, typing_extensions) and the actual findings/KLOC + false-
positives/KLOC metrics computation described in point 79 -- this pass
fixed the measurement *pipeline* and added 3 packages as a proof of
concept, not the full corpus. CPython self-scan (point 80) is still
untouched.

### 83-85. PR/diff mode, GitHub Checks — **NOT ADDRESSED**
`--changed-only`/baseline diffing already existed pre-review; no new
work here.

### 86-89. Score / severity-confidence independence / impact / trigger_conditions — **PARTIAL**
`ScanResult.score` kept (backward compatible) but documented as
deprecated; new `ScanResult.breakdown()` returns
`{high_confidence, medium_confidence, informational, analyzer_errors}`
as suggested. `impact` and `trigger_conditions` machine-readable fields
(sections 88-89) are **DEFERRED**.

### 90-92. Fully data-driven rule representation — **DEFERRED**
Same reasoning as 45-53.

### 93-96. Test suite / local run observations — informational, no action needed
beyond what's already covered above (all counts in this file are from
a real local run, not asserted from memory).

### 97. P0 checklist — see summary at the top; this is what this entire
pass targeted.

### 98-106. P1/P2/positioning/target architecture — **DEFERRED**
Explicitly next-phase per the review's own ordering.

## Files changed in this pass

- `pyrift/finding.py` — new enums (`RuleCategory`, `ContractStatus`,
  `RuntimeVerificationState`, `RuleTier`), multidimensional confidence,
  `contract_status`, `platform_scope`, `context_note` fields.
- `pyrift/rule_metadata.py` — full rewrite: taxonomy, tiers, contract
  status, corrected CPY031/CPY032 evidence, confidence downgrades for
  CPY023/CPY051/PPY035/Tier-B/Tier-C PyPy rules.
- `pyrift/scanner.py` — category-override bug fix; new
  `_apply_guards`/guard-suppression integration; `ScanResult.
  guard_suppressed`; `ScanResult.breakdown()`; `score` documented as
  deprecated.
- `pyrift/analysis/guards.py` — new module (version/implementation
  guards, `TYPE_CHECKING`, import shims).
- `pyrift/rules/cpython/cpy023_multiprocessing_fork.py` — narrowed
  detection, macOS exclusion.
- `pyrift/rules/cpython/cpy031_assert_never.py`,
  `cpy032_reveal_type.py` — corrected evidence citations.
- `benchmark/runtime_harness.py` — honesty rewrite (see section 5).
- `benchmark/run_benchmark.py`, `benchmark/expected.json` — updated
  golden cases/contracts for the above.
- `tests/test_guards.py`, `tests/test_runtime_harness_honesty.py` —
  new (31 new tests total across this file and the ones below).
- `tests/cpython/test_cpy023.py`, `tests/test_coverage_boost.py`,
  `tests/test_false_positives.py`, `tests/test_reporter_extended.py` —
  updated to reflect intentional behavior changes above (old tests that
  encoded the CPY023 false positive and the blanket-"compatibility"
  category bug as "expected" were rewritten, not deleted).

## Suggested next PR (if you want a concrete next step)

1. `# pyrift: ignore RULE -- reason` inline suppression (scoped, not
   built) — natural extension of the guard-suppression pass.
2. `TargetConfig` v2 (`implementations`, `platforms`, `free_threading`,
   `consumer_versions`) as its own PR with a version bump, since it's a
   public API change.
3. Real-world package corpus run (section 79) now that guard/shim
   suppression exists to make the noise level meaningful.
