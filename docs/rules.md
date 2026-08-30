# pyrift — Rule Reference

Complete documentation for all 120 pyrift rules.

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

---

### CPY001 — Dict ordering assumption

**Severity:** Warning | **Confidence:** High | **Affects:** CPython < 3.7, PyPy < 7.3

Comparing `dict.keys()`, `dict.values()`, or `dict.items()` to a list or
tuple assumes insertion order. Only guaranteed on CPython 3.7+ and PyPy 7.3+.

```python
# Bad
assert d.keys() == ['a', 'b']

# Good
assert set(d.keys()) == {'a', 'b'}
```

---

### CPY002 — Exception.add_note() requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10

Added in PEP 678. Raises `AttributeError` on 3.10 and below inside the
except block.

```python
# Bad
except ValueError as e:
    e.add_note("hint")   # AttributeError on 3.10

# Good
if sys.version_info >= (3, 11):
    e.add_note("hint")
```

---

### CPY003 — X | Y union type syntax requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9

PEP 604. Using `X | Y` inside `isinstance()` raises `TypeError` on 3.9 and below.

---

### CPY004 — tomllib requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 680

---

### CPY005 — match/case requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9 | PEP 634

Entire file fails to import on 3.9 — not just the path using `match`.

---

### CPY006 — asyncio.timeout() / TaskGroup requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10

Both added in Python 3.11. Raise `AttributeError` on 3.10 and below.

---

### CPY007 — Module removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.13 | PEP 594

21 legacy modules removed: `aifc`, `audioop`, `cgi`, `cgitb`, `chunk`,
`crypt`, `imghdr`, `mailcap`, `msilib`, `nis`, `nntplib`, `ossaudiodev`,
`pipes`, `sndhdr`, `spwd`, `sunau`, `telnetlib`, `uu`, `xdrlib`,
`asynchat`, `asyncore`, `smtpd`.

---

### CPY008 — __slots__ may not prevent __dict__ with base classes

**Severity:** Info | **Confidence:** High | **Affects:** All versions

If any ancestor class has `__dict__`, `__slots__` on a subclass will NOT
prevent `__dict__` creation.

---

### CPY009 — ExceptionGroup requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 654

---

### CPY010 — @dataclass(slots=True) requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9

The `slots` parameter raises `TypeError` at class definition time on 3.9.

---

### CPY011 — typing.Self requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 673

---

### CPY012 — typing.LiteralString requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 675

---

### CPY013 — typing.override requires Python 3.12+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.11 | PEP 698

---

### CPY014 — typing.TypeAlias requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9 | PEP 613

---

### CPY015 — typing.Never requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 673

---

### CPY016 — typing.TypeVarTuple requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 646

---

### CPY017 — typing.Unpack requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 646

---

### CPY018 — typing.Required / NotRequired requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 655

---

### CPY019 — distutils removed in Python 3.12+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.12 | PEP 632

```python
# Good
from setuptools import setup
```

---

### CPY020 — datetime.UTC requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10

```python
# Good — works on all Python 3
datetime.timezone.utc
```

---

### CPY021 — asyncio.iscoroutinefunction() deprecated since 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.12

Removed in 3.16. Use `inspect.iscoroutinefunction()` instead.

---

### CPY022 — Bitwise inversion on bool deprecated in 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.12

`~True` produces `-2`, not `False`. Removed in 3.16.

---

### CPY023 — multiprocessing default start method changing in 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.14

Runtime-verified: default is `spawn` on Windows in 3.13 and 3.14.
Fork→forkserver change affects Linux/BSD.

---

### CPY024 — typing.TypeGuard requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9 | PEP 647

---

### CPY025 — typing.ParamSpec requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9 | PEP 612

---

### CPY026 — typing.io and typing.re removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.13

```python
# Good
from typing import IO, Pattern
```

---

### CPY027 — locale.resetlocale() removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.13

Runtime-verified: raises `AttributeError` on 3.13 and 3.14.

---

### CPY028 — lib2to3 removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.13

```python
# Good
pip install libcst
```

---

### CPY029 — locals() semantics changed in Python 3.13

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.13 | PEP 667

Modifying `locals()` return value never affects local variables.

---

### CPY030 — sys.path no longer accepts bytes in Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.11

---

### CPY031 — typing.assert_never requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10 | PEP 673

---

### CPY032 — typing.reveal_type requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10

---

### CPY033 — pathlib.Path.is_relative_to() requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8

---

### CPY034 — int.bit_count() requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9

---

### CPY035 — str.removeprefix/removesuffix requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8 | PEP 616

---

### CPY036 — datetime.utcnow() deprecated since Python 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.12

Runtime-verified: raises `DeprecationWarning` on 3.13 and 3.14.

```python
# Good
datetime.datetime.now(datetime.timezone.utc)
```

---

### CPY037 — datetime.utcfromtimestamp() deprecated since Python 3.12

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.12

```python
# Good
datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
```

---

### CPY038 — asyncio.get_event_loop() raises RuntimeError in Python 3.14+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

No longer implicitly creates an event loop.

```python
# Good
asyncio.run(main())
```

---

### CPY039 — zoneinfo module requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8 | PEP 615

---

### CPY040 — graphlib module requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8

---

### CPY041 — dict | merge operator requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8 | PEP 584

Only flagged when at least one operand is a dict literal `{}`.

---

### CPY042 — aiter() and anext() builtins require Python 3.10+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.9

---

### CPY043 — math.lcm() requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8

---

### CPY044 — math.gcd() multi-arg form requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.8

---

### CPY045 — NaN hash behaviour changed in Python 3.10

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.10

---

### CPY046 — open() without encoding= uses platform-dependent encoding before 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≤ 3.14 | PEP 686

UTF-8 on Linux/Mac but often CP1252 on Windows before 3.15.

```python
# Good
open(file, encoding='utf-8')
```

---

### CPY047 — collections.abc.ByteString removed in Python 3.15

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.15

Deprecated in 3.12, removed in 3.15.

```python
# Good
from typing import Union
ByteString = Union[bytes, bytearray, memoryview]
```

---

### CPY048 — concurrent.interpreters requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.13 | PEP 734

---

### CPY049 — compression.zstd requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.13

---

### CPY050 — PurePath.is_reserved() deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.13

Runtime-verified: returns `False` on 3.13 and 3.14 (always was on non-Windows).

```python
# Good
import os; os.path.isreserved(path)
```

---

### CPY051 — Global mutable state unsafe in free-threaded Python 3.13+

**Severity:** Warning | **Confidence:** Medium | **Affects:** CPython ≥ 3.13 (free-threaded) | PEP 703

Module-level `list`, `dict`, `set` literals may be mutated concurrently
without GIL protection in free-threaded builds.

---

### CPY053 — typing.get_overloads() requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.10

---

### CPY054 — int() no longer delegates to __trunc__() in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

Custom numeric types relying on `__trunc__()` for `int()` conversion silently break.

```python
# Good
def __int__(self): return int(self._value)
```

---

### CPY055 — NotImplemented in boolean context raises TypeError in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

Was `DeprecationWarning` since 3.9, now a hard `TypeError`.

---

### CPY057 — pickle default protocol changed to 5 in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.14

Runtime-verified: protocol 4 on 3.13, protocol 5 on 3.14.

```python
# Good — cross-version compatible
pickle.dumps(obj, protocol=4)
```

---

### CPY062 — string.templatelib requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.13 | PEP 750

t-strings are not backportable.

---

### CPY063 — annotationlib requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≤ 3.13 | PEP 749

```python
# Good for 3.13
import typing; typing.get_type_hints(obj)
```

---

### CPY064 — Deprecated AST node types removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

`ast.Num`, `ast.Str`, `ast.Bytes`, `ast.NameConstant`, `ast.Ellipsis` were deprecated in 3.13 and removed in 3.14.

```python
# Bad
isinstance(x, ast.Num)
# Good
isinstance(x, ast.Constant)
```

---

### CPY065 — pkgutil.find_loader()/get_loader() removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

Deprecated in 3.12 (PEP 451), removed in 3.14.

```python
# Good
importlib.util.find_spec('mod')
```

---

### CPY066 — asyncio child watcher classes removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

`ThreadedChildWatcher`, `FastChildWatcher`, etc. removed in 3.14. Use PIDFD-based watching.

---

### CPY067 — typing.NamedTuple keyword syntax deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.13

```python
# Bad
Point = NamedTuple('Point', x=int, y=int)
# Good
class Point(NamedTuple):
    x: int
    y: int
```

---

### CPY068 — typing.no_type_check_decorator deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.13

Use `typing.no_type_check()` instead.

---

### CPY069 — asyncio.iscoroutinefunction() deprecated in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.14

Use `inspect.iscoroutinefunction()` instead.

---

### CPY070 — asyncio event loop policy deprecated in Python 3.14

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.14

`get_event_loop_policy()`, `set_event_loop_policy()`, `DefaultEventLoopPolicy` deprecated. Use `asyncio.run()`.

---

### CPY071 — pty.master_open()/slave_open() removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

Use `pty.openpty()` instead.

---

### CPY072 — importlib.abc resource classes removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

Use `importlib.resources.abc` instead.

---

### CPY073 — sqlite3.version/version_info removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.14

Use `sqlite3.sqlite_version` instead.

---

### CPY074 — code.__lnotab__ deprecated in Python 3.10 (PEP 626)

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.10

Use `code.co_lines()` or `code.co_linetable()` instead.

---

### CPY075 — http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.13

Use `SimpleHTTPRequestHandler` instead.

---

### CPY076 — ssl.wrap_socket() removed in Python 3.12

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.12

Use `SSLContext.wrap_socket()` instead.

---

### CPY077 — typing.TypedDict functional syntax deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Affects:** CPython ≥ 3.13

```python
# Bad
Point = TypedDict('Point', {'x': int})
# Good
class Point(TypedDict):
    x: int
```

---

## PyPy rules — runtime differences

---

### PPY001 — Relying on __del__ for resource cleanup

**Severity:** Error | **Confidence:** High | **Affects:** PyPy all versions

`__del__` may run much later or never on PyPy's tracing GC.
Found in 22 places in CPython's own stdlib (asyncio, tempfile, wave, etc.).

---

### PPY002 — ctypes usage may silently fail on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

Only flagged when dangerous ctypes APIs (CDLL, CFUNCTYPE, Structure, etc.) are used.

---

### PPY003 — sys.getrefcount() is meaningless on PyPy

**Severity:** Error | **Confidence:** High | **Affects:** PyPy all versions

Always returns a dummy constant. Use `gc.get_referrers()` instead.

---

### PPY004 — weakref.proxy() raises ReferenceError unpredictably on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY005 — File write without explicit flush may lose data on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY006 — Monkey-patching built-in types behaves differently on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY007 — sys.intern() identity guarantees differ on PyPy

**Severity:** Info | **Confidence:** Low | **Affects:** PyPy all versions

Observed in practice but not formally documented in PyPy's differences page.

---

### PPY008 — threading.local() cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

Thread-local data persists until GC runs — memory leak risk in servers.

---

### PPY009 — id() values not stable across GC cycles on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY010 — gc.collect() behaviour differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY011 — array.array('u') type code removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Affects:** CPython ≥ 3.13

---

### PPY012 — Overriding built-in methods behaves differently on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY013 — sys.getsizeof() raises TypeError on PyPy

**Severity:** Error | **Confidence:** High | **Affects:** PyPy all versions

PyPy deliberately raises `TypeError`.

---

### PPY014 — String concatenation in loops is O(n²) on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

```python
# Good
result = ''.join(items)
```

---

### PPY015 — Generator cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY016 — Instance __dict__ ordering not guaranteed on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

Not flagged for `self.__dict__` inside class methods — only external access.

---

### PPY017 — Adding __del__ to existing class not called on PyPy

**Severity:** Error | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY018 — sys.setrecursionlimit() behaviour differs on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

Sets stack space to `n * 768` bytes — actual depth ≈ n/5.

---

### PPY019 — float('nan') identity differs between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY021 — Socket not closed promptly on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY022 — PYTHONHASHSEED=0 has no effect on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

PyPy always uses SipHash randomisation regardless of `PYTHONHASHSEED`.

---

### PPY023 — inspect.ismethod() returns different results on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY024 — timeit reports average not minimum on PyPy

**Severity:** Info | **Confidence:** High | **Affects:** PyPy all versions

Only flagged when `timeit()`/`repeat()` result is stored.

---

### PPY025 — Set iteration order differs between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY026 — __builtins__ is always a module on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY027 — Deleting module/class attributes is slower on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY028 — readline.parse_and_bind() silently ignored on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY029 — Assigning to __builtins__ has no effect on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY030 — sys.flags.hash_randomization always 1 on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

Confirmed in official PyPy docs: `-R` is ignored, SipHash always active.
Only `hash_randomization` is flagged — other flags removed from scope.

---

### PPY031 — Integer 'is' identity semantics differ on PyPy

**Severity:** Info | **Confidence:** High | **Affects:** PyPy all versions

Only flagged for large integer literals (> 256) used with `is`.

---

### PPY032 — Mutating dict keys raises RuntimeError on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY033 — Exceptions in __del__ appear at unpredictable times on PyPy

**Severity:** Warning | **Confidence:** Medium | **Affects:** PyPy all versions

---

### PPY034 — hash() values may differ between CPython and PyPy

**Severity:** Info | **Confidence:** High | **Affects:** PyPy all versions

Only flagged when hash result is stored or compared — not when used as dict key.

---

### PPY035 — C extension packages may not work correctly on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

Flags: numpy, pandas, scipy, torch, tensorflow, psycopg2, lxml, Pillow, cv2.

---

### PPY036 — open() line buffering behaves differently on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

---

### PPY037 — os.urandom() source may differ on PyPy

**Severity:** Info | **Confidence:** Low | **Affects:** PyPy all versions

Observed behaviour — not formally documented in PyPy's differences page.

---

### PPY038 — decimal module uses different backend on PyPy

**Severity:** Info | **Confidence:** High | **Affects:** PyPy all versions

Only flagged when decimal context is modified (`getcontext`/`setcontext`).

---

### PPY039 — os.fork() may not work correctly on all PyPy platforms

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy all versions

Observed JIT state issues — not formally documented.

---

### PPY040 — subprocess.PIPE buffering may cause deadlocks on PyPy

**Severity:** Warning | **Confidence:** Low | **Affects:** PyPy all versions

Always use `communicate()` — best practice on all runtimes.

---

### PPY041 — dict | operator requires PyPy 7.3.7+

**Severity:** Info | **Confidence:** High | **Affects:** PyPy < 7.3.7

---

### PPY042 — print(flush=True) may not flush immediately on PyPy

**Severity:** Info | **Confidence:** Low | **Affects:** PyPy all versions

Best practice: call `sys.stdout.flush()` explicitly after critical output.

---

### PPY044 — Exception variable cleanup timing differs on PyPy

**Severity:** Info | **Confidence:** Medium | **Affects:** PyPy all versions

---

### PPY045 — sys.settrace() disables JIT on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

10-100x performance degradation. Affects debuggers and coverage tools.

---

### PPY047 — ctypes.util.find_library() unreliable on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

May return `None` even when library exists. Use cffi instead.

---

### PPY048 — sys.getsizeof() returns different values on PyPy

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

PyPy has different object memory layouts. Do not rely on exact size values.

---

### PPY049 — GC behavior differs between PyPy and CPython

**Severity:** Warning | **Confidence:** High | **Affects:** PyPy all versions

`gc.collect()`, `gc.get_objects()`, `gc.disable()` behave differently. Use context managers instead.

---

### PPY051 — code.__lnotab__ deprecated on PyPy

**Severity:** Warning | **Confidence:** Medium | **Affects:** PyPy all versions

PyPy follows CPython's PEP 626 deprecation. Use `co_lines()` or `co_linetable()`.

---

### PPY052 — importlib.abc resource classes may differ on PyPy

**Severity:** Info | **Confidence:** Low | **Affects:** PyPy all versions

Resource reader interface may have different method signatures. Test on both runtimes.

---

### PPY053 — functools.lru_cache thread safety differs on PyPy

**Severity:** Info | **Confidence:** Low | **Affects:** PyPy all versions

Different locking strategy and cache implementation. Consider explicit thread safety.

---

## Adding your own rules

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the complete guide.

Rule IDs `CPY078+` and `PPY054+` are open for community contributions.