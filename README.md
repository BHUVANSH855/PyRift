## Quick start - Python API

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
    print(f"{error.file}:{error.line} - {error.title}")

# Export formats
json_output     = pyrift.to_json(result)
markdown_output = pyrift.to_markdown(result)
text_output     = pyrift.to_text(result)

# Scan a single file
findings = pyrift.scan_file("./src/utils.py")
```

---

## Rules

### CPython rules - version compatibility

| Rule ID | Title | Runtime | Status |
|---|---|---|---|
| CPY001 | Dict ordering assumption — comparing dict view to ordered sequence | CPython | Active |
| CPY002 | Exception.add_note() requires Python 3.11+ | CPython | Active |
| CPY003 | X | Y union type syntax requires Python 3.10+ | CPython | Active |
| CPY004 | tomllib requires Python 3.11+ | CPython | Active |
| CPY005 | match/case requires Python 3.10+ | CPython | Active |
| CPY006 | asyncio.timeout() / TaskGroup requires Python 3.11+ | CPython | Active |
| CPY007 | Module removed in Python 3.13 | CPython | Active |
| CPY008 | __slots__ may not prevent __dict__ on Python < 3.10 | CPython | Active |
| CPY009 | ExceptionGroup requires Python 3.11+ | CPython | Active |
| CPY010 | @dataclass(slots=True) requires Python 3.10+ | CPython | Active |
| CPY011 | typing.Self requires Python 3.11+ | CPython | Active |
| CPY012 | typing.LiteralString requires Python 3.11+ | CPython | Active |
| CPY013 | typing.override requires Python 3.12+ | CPython | Active |
| CPY014 | typing.TypeAlias requires Python 3.10+ | CPython | Active |
| CPY015 | typing.Never requires Python 3.11+ | CPython | Active |
| CPY016 | typing.TypeVarTuple requires Python 3.11+ | CPython | Active |
| CPY017 | typing.Unpack requires Python 3.11+ | CPython | Active |
| CPY018 | typing.Required / NotRequired requires Python 3.11+ | CPython | Active |
| CPY019 | distutils removed in Python 3.12+ | CPython | Active |
| CPY020 | datetime.UTC requires Python 3.11+ | CPython | Active |
| CPY021 | asyncio.iscoroutinefunction() deprecated since 3.12 | CPython | Active |
| CPY022 | Bitwise inversion on bool (~True/~False) deprecated in 3.12 | CPython | Active |
| CPY023 | multiprocessing default start method changing in Python 3.14 | CPython | Active |
| CPY024 | typing.TypeGuard requires Python 3.10+ | CPython | Active |
| CPY025 | typing.ParamSpec requires Python 3.10+ | CPython | Active |
| CPY026 | typing.io and typing.re removed in Python 3.13 | CPython | Active |
| CPY027 | locale.resetlocale() removed in Python 3.13 | CPython | Active |
| CPY028 | lib2to3 removed in Python 3.13 | CPython | Active |
| CPY029 | locals() semantics changed in Python 3.13 (PEP 667) | CPython | Active |
| CPY030 | sys.path no longer accepts bytes entries in Python 3.11+ | CPython | Active |
| CPY031 | typing.assert_never requires Python 3.11+ | CPython | Active |
| CPY032 | typing.reveal_type requires Python 3.11+ | CPython | Active |
| CPY033 | pathlib.Path.is_relative_to() requires Python 3.9+ | CPython | Active |
| CPY034 | int.bit_count() requires Python 3.10+ | CPython | Active |
| CPY035 | str.removeprefix/removesuffix requires Python 3.9+ | CPython | Active |
| CPY036 | datetime.utcnow() deprecated since Python 3.12 | CPython | Active |
| CPY037 | datetime.utcfromtimestamp() deprecated since Python 3.12 | CPython | Active |
| CPY038 | asyncio.get_event_loop() raises RuntimeError in Python 3.14+ | CPython | Active |
| CPY039 | zoneinfo module requires Python 3.9+ | CPython | Active |
| CPY040 | graphlib module requires Python 3.9+ | CPython | Active |
| CPY041 | dict | merge operator requires Python 3.9+ | CPython | Active |
| CPY042 | aiter() and anext() builtins require Python 3.10+ | CPython | Active |
| CPY043 | math.lcm() requires Python 3.9+ | CPython | Active |
| CPY044 | math.gcd() with multiple args requires Python 3.9+ | CPython | Active |
| CPY045 | NaN hash behaviour changed in Python 3.10 | CPython | Active |
| CPY046 | open() without encoding= uses platform-dependent encoding before 3.15 | CPython | Active |
| CPY047 | collections.abc.ByteString removed in Python 3.15 | CPython | Active |
| CPY048 | concurrent.interpreters requires Python 3.14+ | CPython | Active |
| CPY049 | compression.zstd requires Python 3.14+ | CPython | Active |
| CPY050 | PurePath.is_reserved() deprecated in 3.13, removed in 3.15 | CPython | Active |
| CPY051 | Unsynchronized module-level mutable state may be unsafe in free-threaded Python | CPython | Active |
| CPY053 | typing.get_overloads() requires Python 3.11+ | CPython | Active |
| CPY054 | int() no longer delegates to __trunc__() in Python 3.14 | CPython | Active |
| CPY055 | NotImplemented in boolean context raises TypeError in Python 3.14 | CPython | Active |
| CPY057 | pickle default protocol changed to 5 in Python 3.14 | CPython | Active |
| CPY062 | string.templatelib requires Python 3.14+ | CPython | Active |
| CPY063 | annotationlib requires Python 3.14+ | CPython | Active |

### PyPy rules - runtime differences

| Rule ID | Title | Runtime | Status |
|---|---|---|---|
| PPY001 | Relying on __del__ for resource cleanup breaks on PyPy | PyPy | Active |
| PPY002 | ctypes usage may silently fail on PyPy | PyPy | Active |
| PPY003 | sys.getrefcount() is meaningless on PyPy | PyPy | Active |
| PPY004 | weakref.proxy() lifetime differs on PyPy due to GC model | PyPy | Active |
| PPY005 | File write without explicit lifecycle management on PyPy | PyPy | Active |
| PPY006 | Subclassing built-in types behaves differently on PyPy | PyPy | Active |
| PPY007 | sys.intern() identity guarantees differ on PyPy | PyPy | Active |
| PPY008 | threading.local() cleanup timing differs on PyPy | PyPy | Active |
| PPY009 | id() stability depends on PyPy GC configuration | PyPy | Active |
| PPY010 | gc.collect() behaviour differs on PyPy | PyPy | Active |
| PPY012 | Overriding built-in methods may behave differently on PyPy | PyPy | Active |
| PPY013 | sys.getsizeof() raises TypeError on PyPy | PyPy | Active |
| PPY014 | String concatenation in loop is O(n²) on PyPy | PyPy | Active |
| PPY015 | Generator cleanup timing differs on PyPy | PyPy | Active |
| PPY016 | Instance __dict__ order-sensitive access may differ on PyPy | PyPy | Active |
| PPY017 | Adding __del__ to existing class not called on PyPy | PyPy | Active |
| PPY018 | sys.setrecursionlimit() behaviour differs on PyPy | PyPy | Active |
| PPY019 | float('nan') identity differs between CPython and PyPy | PyPy | Active |
| PPY021 | Socket not closed promptly on PyPy — GC timing | PyPy | Active |
| PPY022 | PYTHONHASHSEED=0 has no effect on PyPy hash randomisation | PyPy | Active |
| PPY023 | inspect.ismethod() returns different results on PyPy | PyPy | Active |
| PPY024 | timeit reports average not minimum on PyPy | PyPy | Active |
| PPY025 | Set iteration order differs between CPython and PyPy | PyPy | Active |
| PPY026 | __builtins__ is always a module on PyPy, never a dict | PyPy | Active |
| PPY027 | Deleting module/class attributes may be slower on PyPy | PyPy | Active |
| PPY028 | readline.parse_and_bind() silently ignored on PyPy | PyPy | Active |
| PPY029 | Assigning to __builtins__ has no effect on PyPy | PyPy | Active |
| PPY030 | sys.flags values may differ between CPython and PyPy | PyPy | Active |
| PPY031 | Integer 'is' identity semantics differ on PyPy | PyPy | Active |
| PPY032 | Mutating dict keys raises RuntimeError on PyPy | PyPy | Active |
| PPY033 | Exceptions in __del__ appear at unpredictable times on PyPy | PyPy | Active |
| PPY034 | hash() values may differ between CPython and PyPy | PyPy | Active |
| PPY035 | C extension packages may not work correctly on PyPy | PyPy | Active |
| PPY036 | open() line buffering behaves differently on PyPy | PyPy | Active |
| PPY037 | os.urandom() source may differ on PyPy | PyPy | Active |
| PPY038 | decimal module uses different backend on PyPy | PyPy | Active |
| PPY039 | os.fork() may not work correctly on all PyPy platforms | PyPy | Active |
| PPY040 | subprocess.PIPE buffering may cause deadlocks on PyPy | PyPy | Active |
| PPY041 | dict | operator requires PyPy 7.3.7+ (Python 3.9 compat) | PyPy | Active |
| PPY042 | print(flush=True) may not flush immediately on PyPy | PyPy | Active |
| PPY044 | Exception variable cleanup timing differs on PyPy | PyPy | Active |
| PPY045 | sys.settrace() disables JIT and is unreliable on PyPy | PyPy | Active |
| PPY047 | ctypes.util.find_library() unreliable on PyPy | PyPy | Active |

### Cross-runtime rules

| Rule ID | Title | Runtime | Status |
|---|---|---|---|
| PPY011 | array.array('u') type code removed in Python 3.13 | Both | Active |

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

Exit code is `1` when errors are found - fails the CI build automatically.
Use `--exit-zero` to report without failing.

---

## Use with pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/BHUVANSH855/pyrift
    rev: v0.8.0
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

PyRift focuses on compatibility and behavioural differences that conventional
linters and type checkers generally do not model. It complements — not
replaces — the tools above.

---

## Git-aware scanning

For maintainer and CI workflows, PyRift can scan only Python files changed
relative to a Git revision (including staged and untracked changes):

```bash
pyrift scan . --changed-only
pyrift scan . --changed-only --base origin/main
```

---

## Features

### Dynamic import detection

Some compatibility issues hide behind imports resolved at runtime rather
than through `import` statements. PyRift detects these too:

- `importlib.import_module("removed_module")`
- `__import__("removed_module")`

Only statically-resolvable module names are flagged; names computed at
runtime from a variable are deliberately left alone to avoid false
positives.

### Version-guard awareness

PyRift understands `sys.version_info` guards. A module import protected by
a `sys.version_info >= (3, N)` check that already covers the required
version is **not** reported, because the guarded code never runs on an
affected interpreter.

### Confidence and evidence

Every finding carries a `confidence` (`high` / `medium` / `low`) and an
`evidence_type` (`official_docs`, `runtime_probe`, `deprecation_warn`,
`pep`, `observed`, `inferred`). These are assigned from a central reviewed
table (`pyrift/rule_metadata.py`); unreviewed rules conservatively default
to `low` / `inferred` rather than over-claiming certainty.

### Multi-name import deduplication

`from tomllib import load, loads` produces a **single** finding, not one
per imported name, so reports stay readable and stable.

### Target-aware filtering

When `pyproject.toml` declares `requires-python`, PyRift drops CPython
findings that cannot affect the project's supported version range. You can
also override with `--python-min` / `--python-max`.

### Rule-robustness guarantee

Every rule is exercised against a broad suite of exotic-but-valid AST
constructs via `benchmark/fuzz_harness.py` to guarantee no rule ever
crashes on valid Python — regardless of finding outcome.

---

## Roadmap

Planned for upcoming versions - contributions welcome:

- `CPY064+` - next CPython compatibility rules (open for contributions)
- `PPY048+` - next PyPy runtime difference rules (open for contributions)
- Pre-commit hook native support
- VS Code extension
- GitHub Action marketplace listing

See [CONTRIBUTING.md](CONTRIBUTING.md) to add a rule yourself. New rule IDs are assigned after reviewing the existing rule inventory to avoid collisions and duplicate coverage.

---

## Contributing

Contributions are very welcome - especially new rules for behaviour differences
you have personally encountered.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Project status

- **Version:** 0.8.0
- **Rules:** 101 total (57 CPython + 43 PyPy + 1 cross-runtime)
- **Tests:** 845 passing
- **Dependencies:** zero
- **Python:** 3.10+

---

## Rule Trustworthiness

Every finding carries a confidence level and evidence type. Rules are
classified into three tiers:

| Tier | Confidence | Evidence | Description |
|---|---|---|---|
| **A** | High | `official_docs` | Verified against official CPython/PyPy documentation |
| **B** | High | `runtime_probe` | Verified via automated runtime probes in `benchmark/runtime_harness.py` |
| **C** | Medium / Low | `observed`, `inferred` | Observed behaviour or inferred from code patterns; needs independent verification |

Unreviewed rules (no entry in `pyrift/rule_metadata.py`) default to
**low** confidence and `inferred` evidence type. See the
[Confidence and evidence](#confidence-and-evidence) feature description
for details.

---

## Known Limitations

- **Static analysis cannot verify runtime behaviour.** PyRift inspects
  ASTs, not executed code. Some findings may be false positives if the
  flagged code is never reached or is guarded at runtime.
- **Some rules are heuristics, not proofs.** A rule may flag code that
  happens to be compatible in practice. Always review findings in context.
- **PyPy rules may become outdated** as PyPy evolves. Report false
  positives so rules can be updated or deprecated.
- **Free-threading rules are experimental.** The CPython 3.13+
  free-threading (no-GIL) build is new and its semantics are still
  stabilising. Rules for free-threaded code may change.
- **Version ranges are conservative.** Affected-version bounds are
  based on documented changes; edge cases or backported fixes may
  alter the actual impact.

---

## Author

Built by [Bhuvansh Kataria](https://github.com/BHUVANSH855) -
CPython contributor and PyPy toolkit author.

---

## License

MIT - see [LICENSE](LICENSE)

## Security

Found a security issue in PyRift itself? Please follow our
[Security Policy](SECURITY.md) and report it privately rather than
opening a public issue.

