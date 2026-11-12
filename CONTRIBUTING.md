# Contributing to PyRift

Thank you for contributing to **PyRift** — a static-analysis scanner that detects **silent Python behaviour differences** across CPython versions and between CPython and PyPy.

The most valuable contributions fix **real compatibility problems**: verified runtime behaviour, a minimal reproduction, a precise AST pattern, and regression tests. Correctness and evidence matter more than finding count.

> Current baseline: `0.8.0` · all registered tests · all registered rules · ~97% coverage. If a section conflicts with the tree, the code is the source of truth — open an issue.

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
├── rules/cpython/  CPY001..CPY078   (version compatibility)
├── rules/pypy/     PPY001..PPY053   (CPython vs PyPy)
├── base_rule.py, finding.py, scanner.py, targets.py
├── rule_metadata.py  (authoritative confidence/evidence)
├── baseline.py, fingerprint.py, git.py, reporter.py, cli.py

tests/  test_*.py + cpython/ and pypy/ (one test module per rule)
benchmark/  run_benchmark.py, expected.json, self_scan.py, corpus.py, runtime_harness.py
compatibility-benchmark/   (historical runtime probe data)
scripts/  generate_docs.py, check_docs.py
docs/rules.md  (auto-generated, all registered rules)
```

Follow the style of the code already present. Update tests + docs alongside any behaviour change.

---

## Finding metadata

Each rule returns `Finding` objects with `severity` (`ERROR`/`WARNING`/`INFO`), `runtime` (`CPYTHON`/`PYPY`/`BOTH`), `affected_from`/`affected_until`, `confidence`, and `evidence`.

**You don't set `confidence`/`evidence` by hand.** Authoritative values live in `pyrift/rule_metadata.py` and are attached automatically via `Finding.__post_init__`.

**Conservation rule:** an unreviewed rule (no `RULE_METADATA` entry) stays at `LOW`/`INFERRED` — it must never claim high confidence silently.

**Rule-ID permanence policy:** once a numeric slot (e.g. `CPY021`) has been used, it is permanent. Retired IDs get a tombstone entry in `RULE_METADATA` with `"status": "tombstone"` and a `"tombstone_reason"` string, and are never reassigned to a new rule. This prevents a user's `--ignore CPY021` suppression from silently suppressing a completely different rule in a future release. When retiring a rule, do **not** delete its metadata entry — replace its `_cpy()`/`_ppy()` call with `_tombstone("<reason>")` and remove the rule from `ALL_RULES` and its source file.

**Intentionality rule:** `evidence_type` and `intent_basis` are separate. A
runtime probe proves that a difference occurs; it does not prove that CPython
intended the difference. Use `documented` for authoritative PEP/official-doc
evidence, `deprecation` for an explicit deprecation/removal path,
`implementation_defined` when the documented contract permits implementation
differences, and `observed`/`inferred` when intent is not established. See
[`docs/behavior-evidence.md`](docs/behavior-evidence.md) for the full model.

---

## Adding a rule — worked example

The following is a complete, end-to-end walkthrough of adding a new CPython rule.
We will add a hypothetical **CPY079** that detects use of `str.removeprefix()` /
`str.removesuffix()`, which were added in Python 3.9.

### Step 1 — Verify the behaviour

Before writing any code, confirm the version bound is real:

```bash
# In a Python 3.8 interpreter:
>>> "hello-world".removeprefix("hello-")
AttributeError: 'str' object has no attribute 'removeprefix'
```

The official reference: [What's New 3.9 — str.removeprefix / removesuffix](https://docs.python.org/3/whatsnew/3.9.html#str-removeprefix-str-removesuffix)

### Step 2 — Create the rule file

```python
# pyrift/rules/cpython/cpy079_str_removeprefix.py
from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Runtime, Severity

if TYPE_CHECKING:
    from pyrift.targets import TargetConfig


_METHODS = frozenset({"removeprefix", "removesuffix"})


class StrRemoveprefixRule(BaseRule):
    """str.removeprefix() / str.removesuffix() require Python 3.9+.

    Use a compatibility shim or guard with sys.version_info for older targets:

        # Python < 3.9 compatible:
        s.removeprefix("x") → s[len("x"):] if s.startswith("x") else s
    """

    rule_id = "CPY079"
    title = "str.removeprefix() / str.removesuffix() require Python 3.9+"
    runtime = "cpython"
    severity = Severity.ERROR

    def check(
        self,
        tree: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _METHODS
            ):
                findings.append(
                    Finding(
                        file=filename,
                        line=node.lineno,
                        col=node.col_offset,
                        rule_id=self.rule_id,
                        title=self.title,
                        description=(
                            f"`str.{node.func.attr}()` was added in Python 3.9. "
                            "Code using it will raise `AttributeError` on 3.8 and earlier."
                        ),
                        severity=self.severity,
                        runtime=Runtime.CPYTHON,
                        affected_from="3.9",
                        suggestion=(
                            "Use `s[len(prefix):]` / `s[:-len(suffix)]` with a "
                            "`startswith`/`endswith` guard, or require Python >= 3.9."
                        ),
                        docs_url="https://docs.python.org/3/whatsnew/3.9.html#str-removeprefix-str-removesuffix",
                    )
                )
        return findings
```

### Step 3 — Register in `pyrift/scanner.py`

```python
# In pyrift/scanner.py, add to ALL_RULES:
from .rules.cpython.cpy079_str_removeprefix import StrRemoveprefixRule

ALL_RULES: list[BaseRule] = [
    # ... existing rules ...
    StrRemoveprefixRule(),
]
```

Confirm the inventory test passes:

```bash
python -m pytest tests/test_rule_inventory.py -q
```

### Step 4 — Add tests

```python
# tests/cpython/test_cpy079.py
from __future__ import annotations

import ast
import textwrap

import pytest

from pyrift.rules.cpython.cpy079_str_removeprefix import StrRemoveprefixRule

rule = StrRemoveprefixRule()


def parse(src: str) -> ast.Module:
    return ast.parse(textwrap.dedent(src))


def run(src: str):
    return rule.check(parse(src), "<test>")


class TestCPY079:
    def test_removeprefix_fires(self):
        findings = run('s.removeprefix("x")')
        assert len(findings) == 1
        assert findings[0].rule_id == "CPY079"

    def test_removesuffix_fires(self):
        findings = run('s.removesuffix("y")')
        assert len(findings) == 1

    def test_other_method_does_not_fire(self):
        assert run('s.strip("x")') == []

    def test_unrelated_call_does_not_fire(self):
        assert run("print('hello')") == []

    def test_chained_call_fires(self):
        findings = run('s.upper().removeprefix("X")')
        assert len(findings) == 1

    def test_nested_call_fires(self):
        findings = run('f(s.removeprefix("x"))')
        assert len(findings) == 1
```

Run the tests:

```bash
python -m pytest tests/cpython/test_cpy079.py -v
```

### Step 5 — Add metadata

```python
# In pyrift/rule_metadata.py, add:
"CPY079": _cpy(
    confidence="high",
    evidence="official_docs",
    contract_status=ContractStatus.DOCUMENTED,
    intent_basis=IntentBasis.DOCUMENTED,
    affected_versions=">=3.9",
    whatsnew_ref="3.9#str-removeprefix-str-removesuffix",
    gh_issue="cpython/issues/39502",
),
```

### Step 6 — Add a benchmark contract

```python
# In benchmark/expected.json, add under "cpython":
{
  "rule_id": "CPY079",
  "title": "str.removeprefix() / str.removesuffix() require Python 3.9+",
  "count": 0
}
```

```bash
python benchmark/run_benchmark.py   # all rules must stay passing
```

### Step 7 — Regenerate docs

```bash
python scripts/generate_docs.py
python scripts/check_docs.py
```

This updates `docs/rules.md` and validates that all test counts are in sync.

### Step 8 — Run the full validation

```bash
python -m ruff check .
python -m mypy pyrift --ignore-missing-imports
python -m pytest tests/ --tb=short -q
python benchmark/self_scan.py      # 0 findings on the project itself
```

---

## Adding a rule (reference steps)

1. **Pick the next free ID** — `CPY079+` or `PPY054+`; never reuse an ID.
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
   python benchmark/run_benchmark.py   # must stay all rules passing, 100% correct
   ```

   Don't weaken existing contracts to make a rule pass.
7. **Update metadata** in `pyrift/rule_metadata.py` — be honest about both
   evidence and intent basis:

   ```python
   "CPYXXX": _metadata("high", "pep:XXXX")
   # Use intent_basis="implementation_defined" when the documented contract
   # explicitly leaves the behavior to the implementation.
   ```
8. **Verify runtime claims** where practical:

   ```bash
   python benchmark/runtime_harness.py
   ```

   Don't claim a runtime difference from memory.
9. **Document the rule** in `docs/rules.md` (what, why, versions, example, fix, official link).

---

## Rule evidence guidelines

Every rule must have honest metadata in `pyrift/rule_metadata.py`.
The evidence type and confidence level determine how much trust users
can place in a finding.

### Evidence types

| Evidence | Meaning | Required for |
|---|---|---|
| `official_docs` | Verified against CPython/PyPy docs or PEP | Tier A (High) |
| `runtime_probe` | Confirmed by `benchmark/runtime_harness.py` | Tier B (High) |
| `deprecation_warn` | Confirmed via deprecation warnings in CPython | Tier A/B |
| `pep` | Described in a PEP with clear version bounds | Tier A |
| `observed` | Reproduced manually, not yet probe-verified | Tier C (Medium) |
| `inferred` | Inferred from code patterns or AST analysis | Tier C (Low) |

### Intent basis

Evidence and intent are separate review questions. Use:

- `documented` when a PEP or official documentation explicitly describes the
  compatibility change.
- `deprecation` when the change follows an explicit deprecation/removal path.
- `implementation_defined` when the documented contract permits
  implementation-specific behavior.
- `observed` when runtime evidence establishes the difference but intent is not
  established.
- `inferred` when neither documentation nor runtime evidence is sufficient.

Do not use a runtime probe alone to label a change intentional.

### How to add a new rule with proper evidence

1. **Start with evidence.** Before writing the rule, verify the behaviour
   you want to detect:
   - Check the official documentation for version-specific changes
   - Run `python benchmark/runtime_harness.py` to probe runtime behaviour
   - Read the relevant PEP for version bounds
2. **Write the rule** following the existing patterns in `pyrift/rules/`.
3. **Add metadata** in `pyrift/rule_metadata.py`:
   ```python
   "CPYXXX": _metadata("high", "official_docs")  # or "runtime_probe", "pep", etc.
   ```
4. **Add tests** covering positive, negative, and edge cases.
5. **Add a benchmark contract** in `benchmark/expected.json`.
6. **Document** in `docs/rules.md`.

### Required evidence for HIGH confidence rules

HIGH confidence requires **one of**:
- `official_docs`: link to the specific documentation page
- `runtime_probe`: passing probe in `benchmark/runtime_harness.py`
- `pep`: reference to the PEP number and section

Rules without verified evidence default to LOW/inferred.

### How to mark rules as deprecated or obsolete

When a rule no longer applies (e.g., the behaviour changed or the
rule was wrong):

1. Remove the rule class from `ALL_RULES` in `pyrift/scanner.py`.
2. Add a comment in the rule file explaining why it was removed:
   ```python
   # CPY052 — REMOVED (wrong detector)
   ```
3. Keep the rule file in the repository for historical reference.
4. Remove the entry from `pyrift/rule_metadata.py`.
5. Remove the rule from `docs/rules.md`.
6. Update counts in README.md and CONTRIBUTING.md.

### Rule lifecycle states

| State | Description |
|---|---|
| **Active** | Registered in `ALL_RULES`, produces findings |
| **Deprecated** | Still registered but may be removed in a future version |
| **Obsolete** | No longer registered; file retained for reference |
| **Removed** | File retained with a REMOVED comment; not in `ALL_RULES` |

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
python benchmark/run_benchmark.py   # golden, all rules passing
python benchmark/self_scan.py       # 0 findings on the project itself
python benchmark/corpus.py          # real-package corpus
python benchmark/runtime_harness.py # runtime probes
```

All applicable checks must pass before opening a PR.

---

## Testing philosophy

Tests define the compatibility contract. They must be deterministic and network-free. Prefer mocking the `git` subprocess for parsing/error-handling tests; use end-to-end tests for real repo behaviour.

---

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature or rule
- `fix:` — Bug fix
- `test:` — Adding or updating tests
- `docs:` — Documentation changes
- `ci:` — CI/CD changes
- `chore:` — Maintenance tasks
- `refactor:` — Code refactoring (no feature change)
- `quality:` — Quality improvements

Examples:
- `feat: add CPY079 rule for <topic>`
- `fix: correct PPY009 false positive on id() as dict key`
- `test: expand edge cases for CPY001`

## Code quality

- `python -m ruff check .` and `git diff --check` must both pass.
- Prefer clear, maintainable Python; keep functions focused.

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
