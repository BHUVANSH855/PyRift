## [0.8.0] â€” 2026-08-26

### Added
- `CPY046` â€” open() without encoding= (platform-dependent before 3.15)
- `CPY047` â€” collections.abc.ByteString removed in Python 3.15
- `CPY048` â€” concurrent.interpreters requires Python 3.14+
- `CPY049` â€” compression.zstd requires Python 3.14+
- `CPY050` â€” PurePath.is_reserved() deprecated in 3.13, removed in 3.15
- `CPY051` â€” Global mutable state unsafe in free-threaded Python 3.13+
- `CPY052` â€” threading.local() atomicity in free-threaded 3.13+
- `CPY053` â€” typing.get_overloads() requires Python 3.11+
- `CPY054` â€” int() no longer delegates to __trunc__() in Python 3.14
- `CPY055` â€” NotImplemented in boolean context raises TypeError in 3.14
- `CPY057` â€” pickle default protocol changed to 5 in Python 3.14
- `CPY062` â€” string.templatelib requires Python 3.14+
- `CPY063` â€” annotationlib requires Python 3.14+
- `PPY046` â€” __debug__ constant behaviour differs with -O on PyPy
- `PPY047` â€” ctypes.util.find_library() unreliable on PyPy
- `pyrift.analysis` â€” shared AST utilities (imports, calls, scope)
- Version-guard awareness â€” imports inside `if sys.version_info >=` not flagged
- Dynamic import detection â€” `importlib.import_module()` and `__import__()`
- Golden benchmark suite â€” 81/81 cases, CI precision gate
- Self-scan quality gate â€” 120 files, 0 findings
- Corpus benchmark â€” reviewed corpus gate covering third-party and standard-library packages
- Runtime differential harness â€” 5 rules verified across 6 Python versions
- Release gate â€” lint, tests, benchmarks, self-scan, corpus, documentation, and package checks must pass before PyPI publish
- Confidence field â€” HIGH/MEDIUM/LOW independent of severity
- `by_statement()` dedup â€” multi-name from imports produce one finding
- BOM-safe scanning â€” utf-8-sig encoding, 0 parse errors on BOM files
- ASCII-safe output â€” no Windows console encoding crashes

### Quality gates & portability
- Rule-robustness fuzz harness (`benchmark/fuzz_harness.py`) â€” 62 constructs
  x 104 rules, zero crashes on valid Python
- Coverage gate â€” CI enforces `--cov-fail-under=95` (overall coverage ~98%)
- CI expands to **Windows and macOS** runners (in addition to Ubuntu) across
  CPython 3.10-3.14 + experimental 3.15 + PyPy 3.11
- Platform-parameterized tests (`tests/test_platform.py`) for OS-sensitive
  rules (CPY046, CPY050, PPY039) validated consistently on Linux/macOS/Windows
- Corpus benchmark expanded 7 â†’ 10 packages (adds `urllib`, `json`,
  `collections`)
- Runtime harness now registers 7 rules (adds CPY022, CPY038) and gracefully
  `[SKIP]`s rules whose probe data is unavailable on a given version
- CPY051 branch coverage raised 86% â†’ 98% (removed dead collector, +26 tests)
- PPY009 now flags `id()` passed to known retaining methods
  (`.append`/`.add`/`.insert`/...) alongside retained/comparison contexts

### Documentation
- README: expanded Git-aware scanning + new "Features" section (dynamic import,
  version-guard awareness, confidence/evidence model, import dedup,
  target-aware filtering, fuzz guarantee)
- `compatibility-benchmark/README.md` documents the probe-data artifacts
- `docs/archive/README.md` indexes superseded reports
- CPY051 docstring documents its conservative synchronization heuristics

### Maintainer & release engineering
- Evidence/confidence drift gate â€” inventory test asserts every rule resolves
  to a supported confidence and unreviewed rules default conservatively
- Version-sync gate â€” `check_docs.py` now verifies
  `__version__` == pyproject == README == CHANGELOG in addition to test count
- Trusted publishing â€” release switched from a long-lived API token to
  OIDC/trusted publishing (`pypa/gh-action-pypi-publish`)
- `py.typed` marker ships in the wheel (PEP 561 typed-package support)
- CI test job parallelizable with `pytest-xdist` (`-n auto`)
- Issue templates (bug report + feature request) and a pull-request template
- README links the Security Policy (SECURITY.md)

### Coverage hardening (iterate-to-10 pass)
- Overall test coverage raised to **99%** (800 tests)
- Rule coverage to 100%: CPY001, CPY023, PPY001; to 95-96%: PPY016, PPY020
- PPY009 raised to 93%; `analysis/imports.py`, `analysis/scope.py` to 100%
- `cli.py` to 98%, `targets.py` to 97%
- Added `tests/test_analysis_imports.py` covering `by_statement`, `alias_for`,
  `has_name_from`, version-guard `get()`, and dynamic-import detection
- Added conservative-default + metadata-validation assertions to the rule
  inventory gate

### Fixed
- CPY057: protocol=None now correctly flagged (same as no protocol)
- CPY057: pickle.Pickler() now detected
- PPY009: no longer flags id() used as dict key or local dedup variable
- PPY043: removed from ALL_RULES (not actionable)
- CPY041: no longer flags bare `a | b` (ambiguous â€” could be bitflags)
- CPY023: no false positive when set_start_method already called
- CPY029: no false positive on print(locals())
- PPY016: no false positive on self.__dict__ inside class methods
- PPY024: only flags when timeit result stored
- PPY034: only flags when hash result stored or compared
- PPY038: only flags when decimal context modified
- cpy050 filename typo fixed (purepatth â†’ purepath)
- 15 BOM-corrupted files stripped
- Duplicate findings from multi-name from imports fixed

### Changed
- 894 tests total
- 22 rules migrated to shared pyrift.analysis utilities
- docs/rules.md auto-generated (104/104 rules documented)
- README stats auto-generated by scripts/generate_docs.py

---

# Changelog

All notable changes to pyrift are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.7.0] â€” 2026-08-25

### Added
- Baseline transparency â€” suppressed finding count now shown in all output formats
- Text output: `Baseline suppressed: N finding(s)` when baseline is active
- JSON output: `baseline_suppressed` field in summary
- Markdown output: `Baseline suppressed` row in summary table

### Changed
- Version bumped to 0.7.0
- `ScanResult` now carries `baseline_suppressed` count
- 392 tests â€” all passing

---

## [0.6.0] â€” 2026-08-25

### Added
- `pyrift/targets.py` â€” target-aware Python version filtering
- `pyrift/baseline.py` â€” baseline engine for suppressing known findings
- `pyrift/fingerprint.py` â€” stable finding fingerprints for baseline matching
- CLI flags: `--python-min`, `--python-max`, `--no-project-config`
- `pyproject.toml` `requires-python` detection for automatic target config
- 76 new tests covering targets, baseline, fingerprinting, CLI, and E2E

### Fixed
- `CPY022` â€” no longer evaluates `~bool` during analysis (was triggering its own deprecation warning)
- `CPY038` â€” corrected version boundary
- `PPY014` â€” reduced false positives (now requires static string evidence)
- `PPY031` â€” hardened identity comparison detection
- `PPY041` â€” expanded test coverage
- `PPY044` â€” reduced noise (only reports when exception variable is used after handler)

### Changed
- Version bumped to 0.6.0
- Scanner now filters findings based on project Python version targets
- 392 tests total

---

## [0.5.0] â€” 2026-08-25

### Added â€” CPython rules
- `CPY019` â€” `distutils` removed in Python 3.12+
- `CPY020` â€” `datetime.UTC` requires Python 3.11+
- `CPY021` â€” `asyncio.iscoroutinefunction()` deprecated since 3.12
- `CPY022` â€” Bitwise inversion on bool deprecated in 3.12
- `CPY023` â€” `multiprocessing` default fork start method changing in 3.14
- `CPY024` â€” `typing.TypeGuard` requires Python 3.10+
- `CPY025` â€” `typing.ParamSpec` requires Python 3.10+
- `CPY026` â€” `typing.io` and `typing.re` removed in Python 3.13
- `CPY027` â€” `locale.resetlocale()` removed in Python 3.13
- `CPY028` â€” `lib2to3` removed in Python 3.13
- `CPY029` â€” `locals()` semantics changed in Python 3.13
- `CPY030` â€” `sys.path` no longer accepts bytes in Python 3.11+
- `CPY031` â€” `typing.assert_never` requires Python 3.11+
- `CPY032` â€” `typing.reveal_type` requires Python 3.11+
- `CPY033` â€” `pathlib.Path.is_relative_to()` requires Python 3.9+
- `CPY034` â€” `int.bit_count()` requires Python 3.10+
- `CPY035` â€” `str.removeprefix/removesuffix` requires Python 3.9+
- `CPY036` â€” `datetime.utcnow()` deprecated since Python 3.12
- `CPY037` â€” `datetime.utcfromtimestamp()` deprecated since Python 3.12
- `CPY038` â€” `asyncio.get_event_loop()` raises RuntimeError in Python 3.12+
- `CPY039` â€” `zoneinfo` module requires Python 3.9+
- `CPY040` â€” `graphlib` module requires Python 3.9+
- `CPY041` â€” dict `|` merge operator requires Python 3.9+
- `CPY042` â€” `aiter()` and `anext()` builtins require Python 3.10+
- `CPY043` â€” `math.lcm()` requires Python 3.9+
- `CPY044` â€” `math.gcd()` multi-arg form requires Python 3.9+
- `CPY045` â€” NaN hash behaviour changed in Python 3.10

### Added â€” PyPy rules
- `PPY008` â€” `threading.local()` cleanup timing differs on PyPy
- `PPY009` â€” `id()` values not stable across GC cycles on PyPy
- `PPY010` â€” `gc.collect()` behaviour differs on PyPy
- `PPY011` â€” `array.array('u')` type code removed in Python 3.13
- `PPY012` â€” Overriding built-in methods behaves differently on PyPy
- `PPY013` â€” `sys.getsizeof()` raises `TypeError` on PyPy
- `PPY014` â€” String concatenation in loops is O(nÂ²) on PyPy
- `PPY015` â€” Generator cleanup timing differs on PyPy
- `PPY016` â€” Instance `__dict__` ordering not guaranteed on PyPy
- `PPY017` â€” Adding `__del__` to existing class not called on PyPy
- `PPY018` â€” `sys.setrecursionlimit()` behaviour differs on PyPy
- `PPY019` â€” `float('nan')` identity differs between CPython and PyPy
- `PPY020` â€” `dict(**kwargs)` requires string keys on PyPy and Python 3
- `PPY021` â€” Socket not closed promptly on PyPy
- `PPY022` â€” `PYTHONHASHSEED=0` has no effect on PyPy
- `PPY023` â€” `inspect.ismethod()` returns different results on PyPy
- `PPY024` â€” `timeit` reports average not minimum on PyPy
- `PPY025` â€” Set iteration order differs between CPython and PyPy
- `PPY026` â€” `__builtins__` is always a module on PyPy
- `PPY027` â€” Deleting module/class attributes is slower on PyPy
- `PPY028` â€” `readline.parse_and_bind()` silently ignored on PyPy
- `PPY029` â€” Assigning to `__builtins__` has no effect on PyPy
- `PPY030` â€” `sys.flags` values may differ between CPython and PyPy
- `PPY031` â€” Integer `is` identity semantics differ on PyPy
- `PPY032` â€” Mutating dict keys raises `RuntimeError` on PyPy
- `PPY033` â€” Exceptions in `__del__` appear at unpredictable times on PyPy
- `PPY034` â€” `hash()` values may differ between CPython and PyPy
- `PPY035` â€” C extension packages may not work correctly on PyPy
- `PPY036` â€” `open()` line buffering behaves differently on PyPy
- `PPY037` â€” `os.urandom()` source may differ on PyPy
- `PPY038` â€” `decimal` module uses different backend on PyPy
- `PPY039` â€” `os.fork()` may not work correctly on all PyPy platforms
- `PPY040` â€” `subprocess.PIPE` buffering may cause deadlocks on PyPy
- `PPY041` â€” dict `|` operator requires PyPy 7.3.7+
- `PPY042` â€” `print(flush=True)` may not flush immediately on PyPy
- `PPY043` â€” `__slots__` memory savings differ on PyPy
- `PPY044` â€” Exception variable cleanup timing differs on PyPy
- `PPY045` â€” `sys.settrace()` disables JIT on PyPy

### Changed
- Version bumped to 0.5.0
- Test suite restructured â€” one file per rule in `tests/cpython/` and `tests/pypy/`
- 316 tests total
- `scanner.py` updated â€” now 90 rules in `ALL_RULES`

---

## [0.4.0] â€” 2026-08-24

### Added
- `CPY011` â€” `typing.Self` requires Python 3.11+ (PEP 673)
- `CPY012` â€” `typing.LiteralString` requires Python 3.11+ (PEP 675)
- `CPY013` â€” `typing.override` requires Python 3.12+ (PEP 698)
- 9 new tests â€” now 79 tests total

### Changed
- Version bumped to 0.4.0
- `scanner.py` updated â€” now 20 rules registered in `ALL_RULES`

---

## [0.3.1] â€” 2026-08-24

### Fixed
- `CPY001` false positive â€” dict view comparisons against `set` and
  `frozenset` are now correctly skipped
- Rule description updated to clarify the actual risk pattern
- 3 new tests added covering the false positive cases â€” now 70 tests

---

## [0.3.0] â€” 2026-08-24

### Added
- `CPY008` â€” `__slots__` may not prevent `__dict__` with non-trivial base classes
- `CPY009` â€” `ExceptionGroup` / `BaseExceptionGroup` requires Python 3.11+ (PEP 654)
- `CPY010` â€” `@dataclass(slots=True)` requires Python 3.10+
- `PPY005` â€” File write without explicit flush may lose data on PyPy
- `PPY006` â€” Monkey-patching built-in types behaves differently on PyPy
- `PPY007` â€” `sys.intern()` identity guarantees differ on PyPy
- Extended test suite â€” now 67 tests
- Complete documentation â€” README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT
- Full rule reference â€” `docs/rules.md`
- GitHub Actions â€” automated tests on Python 3.10, 3.11, 3.12, 3.13
- GitHub Actions â€” automated PyPI publish on version tags

### Changed
- Version bumped to 0.3.0
- `scanner.py` updated â€” now 17 rules registered in `ALL_RULES`

---

## [0.2.0] â€” 2026-08-24

### Added
- `CPY004` â€” `tomllib` requires Python 3.11+ (PEP 680)
- `CPY005` â€” `match/case` structural pattern matching requires Python 3.10+ (PEP 634)
- `CPY006` â€” `asyncio.timeout()` and `asyncio.TaskGroup` require Python 3.11+
- `CPY007` â€” 21 modules removed from stdlib in Python 3.13 (PEP 594)
- `PPY003` â€” `sys.getrefcount()` returns meaningless dummy value on PyPy
- `PPY004` â€” `weakref.proxy()` raises `ReferenceError` unpredictably on PyPy
- Extended test suite â€” now 45 tests

### Changed
- Version bumped to 0.2.0
- `scanner.py` updated â€” now 11 rules registered in `ALL_RULES`

---

## [0.1.0] â€” 2026-08-24

### Added
- Initial release
- `CPY001` â€” Dict ordering assumption
- `CPY002` â€” `Exception.add_note()` requires Python 3.11+
- `CPY003` â€” `X | Y` union type syntax requires Python 3.10+
- `PPY001` â€” Relying on `__del__` for resource cleanup breaks on PyPy
- `PPY002` â€” `ctypes` usage may silently fail on PyPy
- Core scanner engine â€” AST-based, zero dependencies
- CLI â€” `pyrift scan .` with text, JSON, Markdown output
- JSON, Markdown, plain text reporters
- 26 tests passing
- MIT license
