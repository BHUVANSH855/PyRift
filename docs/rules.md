# pyrift — Rule Reference

Complete documentation for all 118 pyrift rules.

## Confidence levels

Each finding carries two independent fields:

| Severity | Meaning |
|---|---|
| `ERROR` | Silent wrong behaviour — crash or data corruption |
| `WARNING` | Different behaviour — may or may not matter |
| `INFO` | Worth knowing — low urgency |

| Confidence | Meaning |
|---|---|
| `HIGH` | Backed by official Python/PyPy docs or confirmed runtime probe |
| `MEDIUM` | Strongly implied by docs or related behaviour |
| `LOW` | Observed in practice — not formally documented |

Rules with `LOW` confidence are still included because the behaviour is real,
but you should verify independently before acting on them.

---

## CPython rules — version compatibility

These rules detect code that behaves differently across CPython versions.

### CPY001 — Dict ordering assumption — comparing dict view to ordered sequence

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY002 — Exception.add_note() requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY003 — X | Y union type syntax requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY004 — tomllib requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY005 — match/case requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY006 — asyncio.timeout() / TaskGroup requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY007 — Module removed in Python 3.13

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY008 — __slots__ may not prevent __dict__ on Python < 3.10

**Severity:** Warning | **Confidence:** Medium | **Affects:** CPython

---
### CPY009 — ExceptionGroup requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY010 — @dataclass(slots=True) requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY011 — typing.Self requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY012 — typing.LiteralString requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY013 — typing.override requires Python 3.12+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY014 — typing.TypeAlias requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY015 — typing.Never requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY016 — typing.TypeVarTuple requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY017 — typing.Unpack requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY018 — typing.Required / NotRequired requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY019 — distutils removed in Python 3.12+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY020 — datetime.UTC requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY022 — Bitwise inversion on bool (~True/~False) deprecated in 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY023 — multiprocessing default start method changing in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY024 — typing.TypeGuard requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY025 — typing.ParamSpec requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY026 — typing.io and typing.re removed in Python 3.13

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY027 — locale.resetlocale() removed in Python 3.13

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY028 — lib2to3 removed in Python 3.13

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY029 — locals() semantics changed in Python 3.13 (PEP 667)

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY030 — sys.path no longer accepts bytes entries in Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY031 — typing.assert_never requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY032 — typing.reveal_type requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY033 — pathlib.Path.is_relative_to() requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY034 — int.bit_count() requires Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY035 — str.removeprefix/removesuffix requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY036 — datetime.utcnow() deprecated since Python 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY037 — datetime.utcfromtimestamp() deprecated since Python 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY038 — asyncio.get_event_loop() raises RuntimeError in Python 3.14+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY039 — zoneinfo module requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY040 — graphlib module requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY041 — dict | merge operator requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY042 — aiter() and anext() builtins require Python 3.10+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY043 — math.lcm() requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY044 — math.gcd() with multiple args requires Python 3.9+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY045 — NaN hash behaviour changed in Python 3.10

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY046 — open() without encoding= uses platform-dependent encoding before 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY047 — collections.abc.ByteString deprecated, scheduled removal in Python 3.17

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY048 — concurrent.interpreters requires Python 3.14+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY049 — compression.zstd requires Python 3.14+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY050 — PurePath.is_reserved() deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY051 — Module-level mutable state may require synchronization in free-threaded Python

**Severity:** Warning | **Confidence:** Medium | **Affects:** CPython

---
### CPY053 — typing.get_overloads() requires Python 3.11+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY054 — int() no longer delegates to __trunc__() in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY055 — NotImplemented in boolean context raises TypeError in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY057 — pickle default protocol changed to 5 in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY062 — string.templatelib requires Python 3.14+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY063 — annotationlib requires Python 3.14+

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY064 — Deprecated AST node types removed in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY065 — pkgutil.find_loader()/get_loader() removed in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY066 — asyncio child watcher classes removed in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY067 — typing.NamedTuple keyword syntax removed in Python 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY068 — typing.no_type_check_decorator deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY069 — asyncio.iscoroutinefunction() deprecated in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY070 — asyncio event loop policy deprecated in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY071 — pty.master_open()/slave_open() removed in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY072 — importlib.abc resource classes removed in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY073 — sqlite3.version/version_info removed in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY074 — code.__lnotab__ deprecated since Python 3.10 (PEP 626)

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY075 — http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY076 — ssl.wrap_socket() removed in Python 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---
### CPY077 — typing.TypedDict zero-field syntax removed in Python 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython

---

---

## PyPy rules — runtime compatibility

These rules detect code that behaves differently on PyPy vs CPython.

### PPY001 — Relying on __del__ for resource cleanup breaks on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY002 — ctypes usage may silently fail on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY003 — sys.getrefcount() is meaningless on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY004 — weakref.proxy() lifetime differs on PyPy due to GC model

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY005 — File write without explicit lifecycle management on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY006 — Monkey-patching built-in types behaves differently on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY007 — sys.intern() identity guarantees differ on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---
### PPY008 — threading.local() cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY009 — id() stability depends on PyPy GC configuration

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY010 — gc.collect() behaviour differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY012 — Overriding built-in methods may behave differently on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY013 — sys.getsizeof() raises TypeError on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY014 — String concatenation in loop is O(n²) on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY015 — Generator cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY016 — Instance __dict__ order-sensitive access may differ on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY017 — Adding __del__ to existing class not called on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY018 — sys.setrecursionlimit() behaviour differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY019 — float('nan') identity differs between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY021 — Socket not closed promptly on PyPy — GC timing

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY022 — PYTHONHASHSEED=0 has no effect on PyPy hash randomisation

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY023 — inspect.ismethod() returns different results on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY024 — timeit reports average not minimum on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY025 — Set iteration order differs between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY026 — __builtins__ is always a module on PyPy, never a dict

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY027 — Deleting module/class attributes may be slower on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY028 — readline.parse_and_bind() silently ignored on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY029 — Assigning to __builtins__ has no effect on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY030 — sys.flags values may differ between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY031 — Integer 'is' identity semantics differ on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY032 — Mutating dict keys raises RuntimeError on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY033 — Exceptions in __del__ appear at unpredictable times on PyPy

**Severity:** Warning | **Confidence:** Medium | **Affects:** PyPy

---
### PPY034 — hash() values may differ between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY035 — C extension packages may not work correctly on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY036 — open() line buffering behaves differently on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY037 — os.urandom() source may differ on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---
### PPY038 — decimal module uses different backend on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY039 — os.fork() may not work correctly on all PyPy platforms

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---
### PPY040 — subprocess.PIPE buffering may cause deadlocks on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---
### PPY041 — dict | operator requires PyPy 7.3.7+ (Python 3.9 compat)

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY042 — print(flush=True) may not flush immediately on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---
### PPY044 — Exception variable cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** Medium | **Affects:** PyPy

---
### PPY045 — sys.settrace() disables JIT and is unreliable on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY047 — ctypes.util.find_library() unreliable on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY049 — GC behavior differs between PyPy and CPython

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy

---
### PPY051 — code.__lnotab__ deprecated on PyPy too

**Severity:** Warning | **Confidence:** Medium | **Affects:** PyPy

---
### PPY052 — importlib.abc resource classes may differ on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---
### PPY053 — functools.lru_cache thread safety differs on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy

---

---

## Cross-runtime rules — CPython & PyPy

These rules apply to both CPython and PyPy.

### PPY011 — array.array('u') type code removed in Python 3.13

**Severity:** Warning | **Confidence:** High | **Affects:** CPython & PyPy

---
