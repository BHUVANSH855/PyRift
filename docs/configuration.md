# Configuration

PyRift can be configured via a `[tool.pyrift]` table in `pyproject.toml`.
All settings are optional — PyRift works with zero project configuration.
When a setting is both in the config file and on the command line, **the
command-line flag always wins**.

## Supported settings

```toml
[tool.pyrift]
# Rule selection — mutually exclusive; omit both to run every rule.
select = ["CPY055", "CPY022"]   # run only these rules
ignore = ["CPY001", "CPY002"]   # run all rules except these

# Output format: "text" (default) | "json" | "markdown" | "sarif" | "github"
format = "json"

# Exit 1 when any finding is produced (useful in CI).
fail_on_findings = true

# Filter to findings backed by a documented/deprecated intent basis.
only_documented = true
```

## Python version note

The `format`, `fail_on_findings`, and `only_documented` settings require
Python 3.11+ (which ships `tomllib` in the standard library) or the
[`tomli`](https://pypi.org/project/tomli/) backport installed in the same
environment.  On Python 3.10 without `tomli`, only `select` and `ignore`
are read from the config file; the other settings silently fall back to
their defaults.

## Example: CI-only failure gate

Keep the local developer experience non-blocking but fail CI:

```toml
[tool.pyrift]
fail_on_findings = true
only_documented = true   # limit noise to intentional CPython changes
```

## Example: project-wide rule ignore list

```toml
[tool.pyrift]
ignore = [
    "CPY001",   # dict ordering — not relevant for this project
    "PPY014",   # PyPy-specific rule
]
```

## Discovering the config file

PyRift walks **upward** from the first scan path looking for
`pyproject.toml`.  The first file found is used, so a monorepo can have
per-package overrides in nested `pyproject.toml` files and a root-level
default in the repository root.
