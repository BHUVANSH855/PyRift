# pyrift

**Detect silent Python behaviour differences across CPython versions and CPython vs PyPy.**

[![PyPI version](https://img.shields.io/pypi/v/pyrift.svg)](https://pypi.org/project/pyrift/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Tests](https://github.com/BHUVANSH855/pyrift/actions/workflows/tests.yml/badge.svg)](https://github.com/BHUVANSH855/pyrift/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pyrift)](https://pypi.org/project/pyrift/)

---

## What is pyrift?

Python upgrades and cross-runtime compatibility (CPython vs PyPy) introduce
**silent behaviour differences** — code that runs without errors but produces
wrong results, leaks resources, or crashes only in certain environments.

These are not syntax errors. Linters won't catch them.
They are not CVEs. Security scanners won't catch them.
They only appear at **runtime**, often in production.

`pyrift` statically detects these patterns before they become bugs.

---

## Install

```bash
pip install pyrift
```

Zero external dependencies. Pure Python. Works on Python 3.10+.

---

## Quick start — CLI

```bash
# Scan current directory
pyrift scan .

# Scan a specific path
pyrift scan ./src

# JSON output (for CI integration)
pyrift scan . --format json

# Markdown report saved to file
pyrift scan . --format markdown --output report.md

# Check version
pyrift --version
```

### Example output

```
[ERROR] src/server.py:42 CPY002: Exception.add_note() requires Python 3.11+
→ Guard with: if sys.version_info >= (3, 11): e.add_note(...)

[ERROR] src/compat.py:17 CPY007: Module removed in Python 3.13
→ Find a third-party replacement for 'cgi' on PyPI

[WARNING] src/resource.py:88 PPY001: Relying on del for resource cleanup breaks on PyPy
→ Use context managers (with statement) or try/finally blocks

Scanned 23 file(s). Found 2 error(s), 1 warning(s). Score: 77/100
```


---

## Quick start — Python API

```python
import pyrift

# Scan a directory
result = pyrift.scan("./src")

print(result)
# ScanResult(files=23, errors=2, warnings=1, score=77)

# Iterate findings
for finding in result.findings:
    print(finding)

# Filter by severity
for error in result.errors:
    print(f"{error.file}:{error.line} — {error.title}")

# Export formats
json_output     = pyrift.to_json(result)
markdown_output = pyrift.to_markdown(result)
text_output     = pyrift.to_text(result)

# Scan a single file
findings = pyrift.scan_file("./src/utils.py")
```

---

## Rules

### CPython rules — version compatibility

| ID | Title | Severity | Affects |
|---|---|---|---|
| CPY001 | Dict ordering assumption | Warning | CPython < 3.7 |
| CPY002 | `Exception.add_note()` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY003 | `X \| Y` union type syntax requires Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY004 | `tomllib` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY005 | `match/case` requires Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY006 | `asyncio.timeout()` / `TaskGroup` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY007 | Module removed in Python 3.13 (21 modules) | Error | CPython ≥ 3.13 |
| CPY008 | `__slots__` may not prevent `__dict__` with base classes | Info | All versions |
| CPY009 | `ExceptionGroup` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY010 | `@dataclass(slots=True)` requires Python 3.10+ | Error | CPython ≤ 3.9 |

### PyPy rules — runtime differences

| ID | Title | Severity | Affects |
|---|---|---|---|
| PPY001 | Relying on `__del__` for resource cleanup | Error | PyPy all versions |
| PPY002 | `ctypes` usage may silently fail | Warning | PyPy all versions |
| PPY003 | `sys.getrefcount()` is meaningless on PyPy | Error | PyPy all versions |
| PPY004 | `weakref.proxy()` raises `ReferenceError` unpredictably | Warning | PyPy all versions |
| PPY005 | File write without explicit flush may lose data | Warning | PyPy all versions |
| PPY006 | Monkey-patching built-in types behaves differently | Warning | PyPy all versions |
| PPY007 | `sys.intern()` identity guarantees differ on PyPy | Warning | PyPy all versions |

Full rule documentation: [docs/rules.md](docs/rules.md)

---

## Use in CI

Add pyrift to your GitHub Actions workflow:

```yaml
- name: Run pyrift
  run: |
    pip install pyrift
    pyrift scan . --format json --output pyrift-report.json
    pyrift scan .
```

Exit code is `1` when errors are found — fails the CI build automatically.
Use `--exit-zero` to report without failing.

---

## Use with pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/BHUVANSH855/pyrift
    rev: v0.3.0
    hooks:
      - id: pyrift
```

---

## Why pyrift?

| Tool | What it catches | What it misses |
|---|---|---|
| `pylint` / `ruff` | Style, common bugs | Runtime behaviour differences |
| `mypy` / `pyright` | Type errors | Runtime behaviour differences |
| `pip-audit` | Known CVEs | Behaviour differences |
| `bandit` | Security patterns | Behaviour differences |
| **`pyrift`** | **Silent runtime behaviour differences** | (that's the whole point) |

pyrift does not replace any of these tools. It catches what they all miss.

---

## Contributing

Contributions are very welcome — especially new rules for behaviour differences
you have personally encountered.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Project status

- **Version:** 0.3.0
- **Rules:** 17 (10 CPython + 7 PyPy)
- **Tests:** 67 passing
- **Dependencies:** zero
- **Python:** 3.10+

---

## Author

Built by [Bhuvansh Kataria](https://github.com/BHUVANSH855) —
CPython contributor and PyPy toolkit author.

---

## License

MIT — see [LICENSE](LICENSE)
