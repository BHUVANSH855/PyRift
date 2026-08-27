# Contributing to pyrift

Thank you for your interest in contributing. pyrift grows through
real-world behaviour differences that developers encounter — your
experience is the most valuable contribution.

---

## Ways to contribute

- **Add a new rule** — the highest-value contribution
- **Improve an existing rule** — reduce false positives, improve suggestions
- **Add test cases** — especially edge cases and real-world code patterns
- **Fix bugs** — open an issue first to discuss
- **Improve documentation** — always welcome

---

## Adding a new rule

This is the most common contribution. Here is the exact process.

### 1. Choose a rule ID

- CPython version compatibility rules: `CPY064`, `CPY065`, ...
- PyPy behaviour difference rules: `PPY048`, `PPY049`, ...

Check `pyrift/scanner.py` for the current highest rule ID.

### 2. Create the rule file

CPython rule → `pyrift/rules/cpython/cpy00X_short_name.py`
PyPy rule → `pyrift/rules/pypy/ppy00X_short_name.py`

Use this template:

```python
"""
CPYXXX — Short title
~~~~~~~~~~~~~~~~~~~~~
One paragraph explaining:
- What the behaviour difference is
- Which versions are affected
- Why it silently fails rather than raising an error immediately
"""
from __future__ import annotations
import ast
from pyrift.base_rule import BaseRule
from pyrift.finding import Finding, Severity, Runtime


class YourRuleName(BaseRule):
    rule_id = "CPYXXX"
    title   = "Short human-readable title"
    runtime = "cpython"  # or "pypy" or "both"

    def check(self, node: ast.AST, filename: str) -> list[Finding]:
        findings: list[Finding] = []

        for n in ast.walk(node):
            # Your AST detection logic here
            if isinstance(n, ast.SomeNode):
                findings.append(Finding(
                    file=filename,
                    line=n.lineno,
                    col=n.col_offset,
                    rule_id=self.rule_id,
                    title=self.title,
                    description="Full explanation of why this is a problem.",
                    severity=Severity.ERROR,   # or WARNING or INFO
                    runtime=Runtime.CPYTHON,   # or PYPY or BOTH
                    affected_from="3.0",
                    affected_until="3.10",
                    suggestion="Concrete actionable fix the developer can apply.",
                    docs_url="https://docs.python.org/...",
                ))

        return findings
```

### 3. Register the rule in scanner.py

Add your import and class instance to `ALL_RULES` in `pyrift/scanner.py`.

### 4. Write tests

Add a test class to `tests/test_pyrift.py`:

```python
class TestCPYXXX:
    rule = YourRuleName()

    def test_detects_the_pattern(self):
        findings = run_rule(self.rule, "code that should trigger the rule")
        assert len(findings) == 1
        assert findings[0].rule_id == "CPYXXX"

    def test_clean_code_no_finding(self):
        findings = run_rule(self.rule, "safe equivalent code")
        assert len(findings) == 0
```

Minimum: one positive test (detects the pattern) and one negative test
(clean code produces no finding).

### 5. Update CHANGELOG.md

Add your rule to the `[Unreleased]` section.

### 6. Submit a pull request

Title format: `feat: add CPYXXX — short description`

---

## Development setup

```bash
git clone https://github.com/BHUVANSH855/PyRift.git
cd PyRift
pip install -e ".[dev]"
```

## Validation commands

Run all of these before submitting a PR:

```bash
# Lint
ruff check .

# Unit tests
pytest tests/ -q

# Golden benchmark — must be 100%
python benchmark/run_benchmark.py

# Self-scan — must produce 0 findings
python benchmark/self_scan.py

# Corpus benchmark
python benchmark/corpus.py

# Update README stats
python scripts/generate_docs.py
```

---

## Rule quality bar

Before submitting, verify your rule:

- Has zero false positives on the pyrift codebase itself
- Has a concrete, actionable suggestion — not just "be careful"
- Has a `docs_url` pointing to official Python or PyPy documentation
- Is grounded in a real behaviour difference — not a style preference
- Has at least one positive and one negative test case
- Has a golden benchmark entry in `benchmark/run_benchmark.py`
- Has a contract in `benchmark/expected.json`
- Is registered in `pyrift/scanner.py` (import + ALL_RULES entry)
- Has metadata in `pyrift/rule_metadata.py`
- Is documented in `docs/rules.md`

---

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
Be respectful and constructive in all interactions.