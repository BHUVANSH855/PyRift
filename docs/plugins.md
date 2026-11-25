# Writing a PyRift Plugin

PyRift supports third-party rule plugins via Python
[entry points](https://packaging.python.org/en/latest/specifications/entry-points/).
A plugin ships as an ordinary Python package and declares a `pyrift.rules`
entry-point group so PyRift discovers it automatically at startup.

---

## Quick start

### 1. Create your rule

```python
# src/pyrift_myplugin/rules.py
from __future__ import annotations

import ast
from typing import Any

from pyrift import BaseRule, Finding, Severity


class MyRule(BaseRule):
    rule_id = "MYP001"
    title = "Example custom rule"
    runtime = "both"      # "cpython" | "pypy" | "both"
    severity = Severity.WARNING

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: Any = None,
    ) -> list[Finding]:
        # Return an empty list when nothing is found.
        return []


def get_rules() -> list[BaseRule]:
    """Entry-point callable — return all rules this plugin provides."""
    return [MyRule()]
```

### 2. Register the entry point

In `pyproject.toml`:

```toml
[project.entry-points."pyrift.rules"]
myplugin = "pyrift_myplugin.rules:get_rules"
```

### 3. Install and run

```bash
pip install -e .          # or publish to PyPI then: pip install pyrift-myplugin
pyrift scan .             # your rules are picked up automatically
```

---

## How discovery works

When PyRift starts, `scanner.py` calls
`importlib.metadata.entry_points(group="pyrift.rules")` and iterates every
registered entry point.  For each one it:

1. Loads the callable (`ep.load()`).
2. Calls it and expects a `list[BaseRule]`.
3. Validates every item is a `BaseRule` instance.
4. Appends valid rules to `ALL_RULES` alongside the built-in CPython and PyPy rules.

If any step raises, PyRift logs a `WARNING` and continues — a broken plugin
never crashes a scan.

---

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| PyPI package | `pyrift-<runtime>` | `pyrift-rustpython` |
| Entry-point name | short slug | `rustpython` |
| Rule IDs | uppercase prefix + digits | `RSP001`, `GRP001` |
| `runtime` attr | lowercase runtime name | `"rustpython"` |

---

## Rules for writing accurate rules

- **Only flag what you can prove from the AST alone.** No runtime execution.
- **Return `[]` when unsure** — a false negative is better than a false positive.
- **Never store state in `self`** — `BaseRule` subclasses cannot define
  `__init__` (enforced at import time). Use `ClassVar` for configuration.
- **Version your plugin** separately from PyRift. If your runtime changes
  behaviour, bump your plugin version and document it.

---

## Full `BaseRule` interface

```python
class BaseRule(ABC):
    rule_id: str           # unique, e.g. "RSP001"
    title: str             # short human description
    runtime: str           # "cpython" | "pypy" | "both" | your runtime name
    category: str          # default "compatibility"
    severity: Severity     # Severity.WARNING | Severity.ERROR | Severity.INFO

    def check(
        self,
        node: ast.AST,
        filename: str,
        target_config: TargetConfig | None = None,
    ) -> list[Finding]: ...
```

See [`pyrift/base_rule.py`](../pyrift/base_rule.py) and
[`pyrift/finding.py`](../pyrift/finding.py) for the full `Finding` constructor.
