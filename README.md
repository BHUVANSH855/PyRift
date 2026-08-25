
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
| CPY011 | `typing.Self` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY012 | `typing.LiteralString` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY013 | `typing.override` requires Python 3.12+ | Error | CPython ≤ 3.11 |
| CPY014 | `typing.TypeAlias` requires Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY015 | `typing.Never` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY016 | `typing.TypeVarTuple` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY017 | `typing.Unpack` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY018 | `typing.Required` / `NotRequired` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY019 | `distutils` removed in Python 3.12+ | Error | CPython ≥ 3.12 |
| CPY020 | `datetime.UTC` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY021 | `asyncio.iscoroutinefunction()` deprecated since 3.12 | Warning | CPython ≥ 3.12 |
| CPY022 | Bitwise inversion on bool deprecated in 3.12 | Warning | CPython ≥ 3.12 |
| CPY023 | `multiprocessing` default start method changing in 3.14 | Warning | CPython ≥ 3.14 |
| CPY024 | `typing.TypeGuard` requires Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY025 | `typing.ParamSpec` requires Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY026 | `typing.io` and `typing.re` removed in Python 3.13 | Error | CPython ≥ 3.13 |
| CPY027 | `locale.resetlocale()` removed in Python 3.13 | Error | CPython ≥ 3.13 |
| CPY028 | `lib2to3` removed in Python 3.13 | Error | CPython ≥ 3.13 |
| CPY029 | `locals()` semantics changed in Python 3.13 | Warning | CPython ≥ 3.13 |
| CPY030 | `sys.path` no longer accepts bytes in Python 3.11+ | Error | CPython ≥ 3.11 |
| CPY031 | `typing.assert_never` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY032 | `typing.reveal_type` requires Python 3.11+ | Error | CPython ≤ 3.10 |
| CPY033 | `pathlib.Path.is_relative_to()` requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY034 | `int.bit_count()` requires Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY035 | `str.removeprefix/removesuffix` requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY036 | `datetime.utcnow()` deprecated since Python 3.12 | Warning | CPython ≥ 3.12 |
| CPY037 | `datetime.utcfromtimestamp()` deprecated since Python 3.12 | Warning | CPython ≥ 3.12 |
| CPY038 | `asyncio.get_event_loop()` raises RuntimeError in 3.12+ | Error | CPython ≥ 3.12 |
| CPY039 | `zoneinfo` module requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY040 | `graphlib` module requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY041 | dict `\|` merge operator requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY042 | `aiter()` and `anext()` builtins require Python 3.10+ | Error | CPython ≤ 3.9 |
| CPY043 | `math.lcm()` requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY044 | `math.gcd()` multi-arg form requires Python 3.9+ | Error | CPython ≤ 3.8 |
| CPY045 | NaN hash behaviour changed in Python 3.10 | Warning | CPython ≥ 3.10 |

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
| PPY008 | `threading.local()` cleanup timing differs on PyPy | Warning | PyPy all versions |
| PPY009 | `id()` values not stable across GC cycles on PyPy | Warning | PyPy all versions |
| PPY010 | `gc.collect()` behaviour differs on PyPy | Warning | PyPy all versions |
| PPY011 | `array.array('u')` type code removed in Python 3.13 | Error | CPython ≥ 3.13 |
| PPY012 | Overriding built-in methods behaves differently on PyPy | Warning | PyPy all versions |
| PPY013 | `sys.getsizeof()` raises `TypeError` on PyPy | Error | PyPy all versions |
| PPY014 | String concatenation in loops is O(n²) on PyPy | Warning | PyPy all versions |
| PPY015 | Generator cleanup timing differs on PyPy | Warning | PyPy all versions |
| PPY016 | Instance `__dict__` ordering not guaranteed on PyPy | Warning | PyPy all versions |
| PPY017 | Adding `__del__` to existing class not called on PyPy | Error | PyPy all versions |
| PPY018 | `sys.setrecursionlimit()` behaviour differs on PyPy | Warning | PyPy all versions |
| PPY019 | `float('nan')` identity differs between CPython and PyPy | Warning | PyPy all versions |
| PPY020 | `dict(**kwargs)` requires string keys on PyPy | Error | PyPy all versions |
| PPY021 | Socket not closed promptly on PyPy | Warning | PyPy all versions |
| PPY022 | `PYTHONHASHSEED=0` has no effect on PyPy | Warning | PyPy all versions |
| PPY023 | `inspect.ismethod()` returns different results on PyPy | Warning | PyPy all versions |
| PPY024 | `timeit` reports average not minimum on PyPy | Info | PyPy all versions |
| PPY025 | Set iteration order differs between CPython and PyPy | Warning | PyPy all versions |
| PPY026 | `__builtins__` is always a module on PyPy | Warning | PyPy all versions |
| PPY027 | Deleting module/class attributes is slower on PyPy | Warning | PyPy all versions |
| PPY028 | `readline.parse_and_bind()` silently ignored on PyPy | Warning | PyPy all versions |
| PPY029 | Assigning to `__builtins__` has no effect on PyPy | Warning | PyPy all versions |
| PPY030 | `sys.flags` values may differ between CPython and PyPy | Warning | PyPy all versions |
| PPY031 | Integer `is` identity semantics differ on PyPy | Info | PyPy all versions |
| PPY032 | Mutating dict keys raises `RuntimeError` on PyPy | Warning | PyPy all versions |
| PPY033 | Exceptions in `__del__` appear at unpredictable times | Warning | PyPy all versions |
| PPY034 | `hash()` values may differ between CPython and PyPy | Info | PyPy all versions |
| PPY035 | C extension packages may not work correctly on PyPy | Warning | PyPy all versions |
| PPY036 | `open()` line buffering behaves differently on PyPy | Warning | PyPy all versions |
| PPY037 | `os.urandom()` source may differ on PyPy | Info | PyPy all versions |
| PPY038 | `decimal` module uses different backend on PyPy | Info | PyPy all versions |
| PPY039 | `os.fork()` may not work correctly on all PyPy platforms | Warning | PyPy all versions |
| PPY040 | `subprocess.PIPE` buffering may cause deadlocks on PyPy | Warning | PyPy all versions |
| PPY041 | dict `\|` operator requires PyPy 7.3.7+ | Info | PyPy < 7.3.7 |
| PPY042 | `print(flush=True)` may not flush immediately on PyPy | Info | PyPy all versions |
| PPY043 | `__slots__` memory savings differ on PyPy | Info | PyPy all versions |
| PPY044 | Exception variable cleanup timing differs on PyPy | Info | PyPy all versions |
| PPY045 | `sys.settrace()` disables JIT on PyPy | Warning | PyPy all versions |

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
    rev: v0.7.0
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

## Roadmap

Planned for upcoming versions — contributions welcome:

- `CPY046` — `typing.TypeIs` requires Python 3.13+
- `CPY047` — `typing.ReadOnly` requires Python 3.13+
- Pre-commit hook native support
- VS Code extension
- GitHub Action marketplace listing

See [CONTRIBUTING.md](CONTRIBUTING.md) to add a rule yourself — rule IDs
`CPY046+` and `PPY046+` are open for community contributions.

---

## Contributing

Contributions are very welcome — especially new rules for behaviour differences
you have personally encountered.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Project status

- **Version:** 0.7.0
- **Rules:** 90 (45 CPython + 45 PyPy)
- **Tests:** 392 passing
- **Dependencies:** zero
- **Python:** 3.10+

---

## Author

Built by [Bhuvansh Kataria](https://github.com/BHUVANSH855) —
CPython contributor and PyPy toolkit author.

---

## License

MIT — see [LICENSE](LICENSE)