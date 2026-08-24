# Changelog

All notable changes to pyrift are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

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