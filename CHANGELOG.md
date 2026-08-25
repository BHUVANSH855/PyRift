# Changelog

All notable changes to pyrift are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.6.0] — 2026-08-25

### Added
- `pyrift/targets.py` — target-aware Python version filtering
- `pyrift/baseline.py` — baseline engine for suppressing known findings
- `pyrift/fingerprint.py` — stable finding fingerprints for baseline matching
- CLI flags: `--python-min`, `--python-max`, `--no-project-config`
- `pyproject.toml` `requires-python` detection for automatic target config
- 76 new tests covering targets, baseline, fingerprinting, CLI, and E2E

### Fixed
- `CPY022` — no longer evaluates `~bool` during analysis (was triggering its own deprecation warning)
- `CPY038` — corrected version boundary
- `PPY014` — reduced false positives (now requires static string evidence)
- `PPY031` — hardened identity comparison detection
- `PPY041` — expanded test coverage
- `PPY044` — reduced noise (only reports when exception variable is used after handler)

### Changed
- Version bumped to 0.6.0
- Scanner now filters findings based on project Python version targets
- 392 tests total

---

## [0.5.0] — 2026-08-25

### Added — CPython rules
- `CPY019` — `distutils` removed in Python 3.12+
- `CPY020` — `datetime.UTC` requires Python 3.11+
- `CPY021` — `asyncio.iscoroutinefunction()` deprecated since 3.12
- `CPY022` — Bitwise inversion on bool deprecated in 3.12
- `CPY023` — `multiprocessing` default fork start method changing in 3.14
- `CPY024` — `typing.TypeGuard` requires Python 3.10+
- `CPY025` — `typing.ParamSpec` requires Python 3.10+
- `CPY026` — `typing.io` and `typing.re` removed in Python 3.13
- `CPY027` — `locale.resetlocale()` removed in Python 3.13
- `CPY028` — `lib2to3` removed in Python 3.13
- `CPY029` — `locals()` semantics changed in Python 3.13
- `CPY030` — `sys.path` no longer accepts bytes in Python 3.11+
- `CPY031` — `typing.assert_never` requires Python 3.11+
- `CPY032` — `typing.reveal_type` requires Python 3.11+
- `CPY033` — `pathlib.Path.is_relative_to()` requires Python 3.9+
- `CPY034` — `int.bit_count()` requires Python 3.10+
- `CPY035` — `str.removeprefix/removesuffix` requires Python 3.9+
- `CPY036` — `datetime.utcnow()` deprecated since Python 3.12
- `CPY037` — `datetime.utcfromtimestamp()` deprecated since Python 3.12
- `CPY038` — `asyncio.get_event_loop()` raises RuntimeError in Python 3.12+
- `CPY039` — `zoneinfo` module requires Python 3.9+
- `CPY040` — `graphlib` module requires Python 3.9+
- `CPY041` — dict `|` merge operator requires Python 3.9+
- `CPY042` — `aiter()` and `anext()` builtins require Python 3.10+
- `CPY043` — `math.lcm()` requires Python 3.9+
- `CPY044` — `math.gcd()` multi-arg form requires Python 3.9+
- `CPY045` — NaN hash behaviour changed in Python 3.10

### Added — PyPy rules
- `PPY008` — `threading.local()` cleanup timing differs on PyPy
- `PPY009` — `id()` values not stable across GC cycles on PyPy
- `PPY010` — `gc.collect()` behaviour differs on PyPy
- `PPY011` — `array.array('u')` type code removed in Python 3.13
- `PPY012` — Overriding built-in methods behaves differently on PyPy
- `PPY013` — `sys.getsizeof()` raises `TypeError` on PyPy
- `PPY014` — String concatenation in loops is O(n²) on PyPy
- `PPY015` — Generator cleanup timing differs on PyPy
- `PPY016` — Instance `__dict__` ordering not guaranteed on PyPy
- `PPY017` — Adding `__del__` to existing class not called on PyPy
- `PPY018` — `sys.setrecursionlimit()` behaviour differs on PyPy
- `PPY019` — `float('nan')` identity differs between CPython and PyPy
- `PPY020` — `dict(**kwargs)` requires string keys on PyPy and Python 3
- `PPY021` — Socket not closed promptly on PyPy
- `PPY022` — `PYTHONHASHSEED=0` has no effect on PyPy
- `PPY023` — `inspect.ismethod()` returns different results on PyPy
- `PPY024` — `timeit` reports average not minimum on PyPy
- `PPY025` — Set iteration order differs between CPython and PyPy
- `PPY026` — `__builtins__` is always a module on PyPy
- `PPY027` — Deleting module/class attributes is slower on PyPy
- `PPY028` — `readline.parse_and_bind()` silently ignored on PyPy
- `PPY029` — Assigning to `__builtins__` has no effect on PyPy
- `PPY030` — `sys.flags` values may differ between CPython and PyPy
- `PPY031` — Integer `is` identity semantics differ on PyPy
- `PPY032` — Mutating dict keys raises `RuntimeError` on PyPy
- `PPY033` — Exceptions in `__del__` appear at unpredictable times on PyPy
- `PPY034` — `hash()` values may differ between CPython and PyPy
- `PPY035` — C extension packages may not work correctly on PyPy
- `PPY036` — `open()` line buffering behaves differently on PyPy
- `PPY037` — `os.urandom()` source may differ on PyPy
- `PPY038` — `decimal` module uses different backend on PyPy
- `PPY039` — `os.fork()` may not work correctly on all PyPy platforms
- `PPY040` — `subprocess.PIPE` buffering may cause deadlocks on PyPy
- `PPY041` — dict `|` operator requires PyPy 7.3.7+
- `PPY042` — `print(flush=True)` may not flush immediately on PyPy
- `PPY043` — `__slots__` memory savings differ on PyPy
- `PPY044` — Exception variable cleanup timing differs on PyPy
- `PPY045` — `sys.settrace()` disables JIT on PyPy

### Changed
- Version bumped to 0.6.0
- Test suite restructured — one file per rule in `tests/cpython/` and `tests/pypy/`
- 316 tests total
- `scanner.py` updated — now 90 rules in `ALL_RULES`

---

## [0.4.0] — 2026-08-24

### Added
- `CPY011` — `typing.Self` requires Python 3.11+ (PEP 673)
- `CPY012` — `typing.LiteralString` requires Python 3.11+ (PEP 675)
- `CPY013` — `typing.override` requires Python 3.12+ (PEP 698)
- 9 new tests — now 79 tests total

### Changed
- Version bumped to 0.4.0
- `scanner.py` updated — now 20 rules registered in `ALL_RULES`

---

## [0.3.1] — 2026-08-24

### Fixed
- `CPY001` false positive — dict view comparisons against `set` and
  `frozenset` are now correctly skipped
- Rule description updated to clarify the actual risk pattern
- 3 new tests added covering the false positive cases — now 70 tests

---

## [0.3.0] — 2026-08-24

### Added
- `CPY008` — `__slots__` may not prevent `__dict__` with non-trivial base classes
- `CPY009` — `ExceptionGroup` / `BaseExceptionGroup` requires Python 3.11+ (PEP 654)
- `CPY010` — `@dataclass(slots=True)` requires Python 3.10+
- `PPY005` — File write without explicit flush may lose data on PyPy
- `PPY006` — Monkey-patching built-in types behaves differently on PyPy
- `PPY007` — `sys.intern()` identity guarantees differ on PyPy
- Extended test suite — now 67 tests
- Complete documentation — README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT
- Full rule reference — `docs/rules.md`
- GitHub Actions — automated tests on Python 3.10, 3.11, 3.12, 3.13
- GitHub Actions — automated PyPI publish on version tags

### Changed
- Version bumped to 0.3.0
- `scanner.py` updated — now 17 rules registered in `ALL_RULES`

---

## [0.2.0] — 2026-08-24

### Added
- `CPY004` — `tomllib` requires Python 3.11+ (PEP 680)
- `CPY005` — `match/case` structural pattern matching requires Python 3.10+ (PEP 634)
- `CPY006` — `asyncio.timeout()` and `asyncio.TaskGroup` require Python 3.11+
- `CPY007` — 21 modules removed from stdlib in Python 3.13 (PEP 594)
- `PPY003` — `sys.getrefcount()` returns meaningless dummy value on PyPy
- `PPY004` — `weakref.proxy()` raises `ReferenceError` unpredictably on PyPy
- Extended test suite — now 45 tests

### Changed
- Version bumped to 0.2.0
- `scanner.py` updated — now 11 rules registered in `ALL_RULES`

---

## [0.1.0] — 2026-08-24

### Added
- Initial release
- `CPY001` — Dict ordering assumption
- `CPY002` — `Exception.add_note()` requires Python 3.11+
- `CPY003` — `X | Y` union type syntax requires Python 3.10+
- `PPY001` — Relying on `__del__` for resource cleanup breaks on PyPy
- `PPY002` — `ctypes` usage may silently fail on PyPy
- Core scanner engine — AST-based, zero dependencies
- CLI — `pyrift scan .` with text, JSON, Markdown output
- JSON, Markdown, plain text reporters
- 26 tests passing
- MIT license