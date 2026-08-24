# pyrift — Rule Reference

Complete documentation for all 90 pyrift rules.

---

## CPython rules — version compatibility

These rules detect code that behaves differently across CPython versions.

---

### CPY001 — Dict ordering assumption

**Severity:** Warning | **Affects:** CPython < 3.7, PyPy < 7.3

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

**Severity:** Error | **Affects:** CPython ≤ 3.10

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

**Severity:** Error | **Affects:** CPython ≤ 3.9

PEP 604. Using `X | Y` inside `isinstance()` raises `TypeError` on 3.9 and below.

```python
# Bad
isinstance(x, int | str)

# Good
isinstance(x, (int, str))
```

---

### CPY004 — tomllib requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

Added in PEP 680. Raises `ModuleNotFoundError` on 3.10 and below.

```python
# Good
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
```

---

### CPY005 — match/case requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9

PEP 634. Entire file fails to import on 3.9 — not just the path using `match`.

---

### CPY006 — asyncio.timeout() / TaskGroup requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

Both added in Python 3.11. Raise `AttributeError` on 3.10 and below.

```python
# Good
await asyncio.wait_for(coro(), timeout=5.0)
```

---

### CPY007 — Module removed in Python 3.13

**Severity:** Error | **Affects:** CPython ≥ 3.13

PEP 594 removed 21 legacy modules: `aifc`, `audioop`, `cgi`, `cgitb`,
`chunk`, `crypt`, `imghdr`, `mailcap`, `msilib`, `nis`, `nntplib`,
`ossaudiodev`, `pipes`, `sndhdr`, `spwd`, `sunau`, `telnetlib`, `uu`,
`xdrlib`, `asynchat`, `asyncore`, `smtpd`.

---

### CPY008 — __slots__ may not prevent __dict__ with base classes

**Severity:** Info | **Affects:** All versions

If any ancestor class has `__dict__`, `__slots__` on a subclass will NOT
prevent `__dict__` creation.

```python
# Safe — all ancestors define __slots__
class Base:
    __slots__ = ()
class Child(Base):
    __slots__ = ['x']
```

---

### CPY009 — ExceptionGroup requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

PEP 654. Both `ExceptionGroup` and `BaseExceptionGroup` raise `NameError`
on 3.10 and below.

---

### CPY010 — @dataclass(slots=True) requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9

The `slots` parameter raises `TypeError` at class definition time on 3.9.

---

### CPY011 — typing.Self requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

PEP 673. Raises `ImportError` on 3.10 and below.

```python
# Good
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self
```

---

### CPY012 — typing.LiteralString requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10 | PEP 675

---

### CPY013 — typing.override requires Python 3.12+

**Severity:** Error | **Affects:** CPython ≤ 3.11 | PEP 698

---

### CPY014 — typing.TypeAlias requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9 | PEP 613

---

### CPY015 — typing.Never requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10 | PEP 673

---

### CPY016 — typing.TypeVarTuple requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10 | PEP 646

---

### CPY017 — typing.Unpack requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10 | PEP 646

---

### CPY018 — typing.Required / NotRequired requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10 | PEP 655

---

### CPY019 — distutils removed in Python 3.12+

**Severity:** Error | **Affects:** CPython ≥ 3.12 | PEP 632

```python
# Good
from setuptools import setup
```

---

### CPY020 — datetime.UTC requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

```python
# Good — works on all Python 3
datetime.timezone.utc
```

---

### CPY021 — asyncio.iscoroutinefunction() deprecated since 3.12

**Severity:** Warning | **Affects:** CPython ≥ 3.12

Removed in 3.16. Use `inspect.iscoroutinefunction()` instead.

---

### CPY022 — Bitwise inversion on bool deprecated in 3.12

**Severity:** Warning | **Affects:** CPython ≥ 3.12

`~True` produces `-2`, not `False`. Removed in 3.16.

```python
# Good
not True   # False
```

---

### CPY023 — multiprocessing default start method changing in 3.14

**Severity:** Warning | **Affects:** CPython ≥ 3.14

Default changes from `fork` to a safer method on Linux/BSD.

```python
# Good — explicit
multiprocessing.set_start_method('fork')
```

---

### CPY024 — typing.TypeGuard requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9 | PEP 647

---

### CPY025 — typing.ParamSpec requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9 | PEP 612

---

### CPY026 — typing.io and typing.re removed in Python 3.13

**Severity:** Error | **Affects:** CPython ≥ 3.13

```python
# Good
from typing import IO, Pattern
```

---

### CPY027 — locale.resetlocale() removed in Python 3.13

**Severity:** Error | **Affects:** CPython ≥ 3.13

```python
# Good
locale.setlocale(locale.LC_ALL, '')
```

---

### CPY028 — lib2to3 removed in Python 3.13

**Severity:** Error | **Affects:** CPython ≥ 3.13

```python
# Good
pip install libcst
```

---

### CPY029 — locals() semantics changed in Python 3.13

**Severity:** Warning | **Affects:** CPython ≥ 3.13

PEP 667. Modifying `locals()` return value never affects local variables.

---

### CPY030 — sys.path no longer accepts bytes in Python 3.11+

**Severity:** Error | **Affects:** CPython ≥ 3.11

```python
# Good
sys.path.append('/some/path')
```

---

### CPY031 — typing.assert_never requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10 | PEP 673

---

### CPY032 — typing.reveal_type requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

Was only a type-checker special form before 3.11.

---

### CPY033 — pathlib.Path.is_relative_to() requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8

```python
# Good for 3.8
try:
    path.relative_to(base); return True
except ValueError:
    return False
```

---

### CPY034 — int.bit_count() requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9

```python
# Good for 3.9
bin(n).count('1')
```

---

### CPY035 — str.removeprefix/removesuffix requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8 | PEP 616

```python
# Good for 3.8
s[len(prefix):] if s.startswith(prefix) else s
```

---

### CPY036 — datetime.utcnow() deprecated since Python 3.12

**Severity:** Warning | **Affects:** CPython ≥ 3.12

Returns a naive datetime with no timezone info.

```python
# Good
datetime.datetime.now(datetime.timezone.utc)
```

---

### CPY037 — datetime.utcfromtimestamp() deprecated since Python 3.12

**Severity:** Warning | **Affects:** CPython ≥ 3.12

```python
# Good
datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
```

---

### CPY038 — asyncio.get_event_loop() raises RuntimeError in Python 3.12+

**Severity:** Error | **Affects:** CPython ≥ 3.12

No longer implicitly creates an event loop.

```python
# Good
asyncio.run(main())
```

---

### CPY039 — zoneinfo module requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8 | PEP 615

```python
# Good for 3.8
from backports.zoneinfo import ZoneInfo
```

---

### CPY040 — graphlib module requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8

`graphlib.TopologicalSorter` added in Python 3.9.

---

### CPY041 — dict | merge operator requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8 | PEP 584

```python
# Good for 3.8
{**d1, **d2}
```

---

### CPY042 — aiter() and anext() builtins require Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9

Raise `NameError` on 3.9 and below.

---

### CPY043 — math.lcm() requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8

```python
# Good for 3.8
def lcm(a, b): return abs(a*b) // math.gcd(a, b)
```

---

### CPY044 — math.gcd() multi-arg form requires Python 3.9+

**Severity:** Error | **Affects:** CPython ≤ 3.8

Calling with 3+ args raises `TypeError` on 3.8.

```python
# Good for 3.8
from functools import reduce
reduce(math.gcd, [a, b, c])
```

---

### CPY045 — NaN hash behaviour changed in Python 3.10

**Severity:** Warning | **Affects:** CPython ≥ 3.10

Before 3.10, `hash(float('nan'))` always returned 0. Now depends on object identity.

---

## PyPy rules — runtime differences

---

### PPY001 — Relying on __del__ for resource cleanup

**Severity:** Error | **Affects:** PyPy all versions

`__del__` may run much later or never on PyPy's tracing GC.

```python
# Good
class Conn:
    def __enter__(self): return self
    def __exit__(self, *a): self.socket.close()
```

---

### PPY002 — ctypes usage may silently fail on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

PyPy's ctypes is incomplete. Use `cffi` instead.

---

### PPY003 — sys.getrefcount() is meaningless on PyPy

**Severity:** Error | **Affects:** PyPy all versions

Always returns a dummy constant. Use `gc.get_referrers()` instead.

---

### PPY004 — weakref.proxy() raises ReferenceError unpredictably on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
ref = weakref.ref(obj)
target = ref()
if target is not None:
    target.method()
```

---

### PPY005 — File write without explicit flush may lose data on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
with open('out.txt', 'w') as f:
    f.write(data)
```

---

### PPY006 — Monkey-patching built-in types behaves differently on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
class MyList(list):
    def custom(self): pass
```

---

### PPY007 — sys.intern() identity guarantees differ on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
assert a == b   # not: a is b
```

---

### PPY008 — threading.local() cleanup timing differs on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

Thread-local data persists until GC runs — causes memory leaks with
many short-lived threads.

---

### PPY009 — id() values not stable across GC cycles on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
x is y   # not: id(x) == id(y)
```

---

### PPY010 — gc.collect() behaviour differs on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

Cleanup is not guaranteed to be immediate. Use context managers instead.

---

### PPY011 — array.array('u') type code removed in Python 3.13

**Severity:** Error | **Affects:** CPython ≥ 3.13

```python
# Good
array.array('w', ...)
```

---

### PPY012 — Overriding built-in methods behaves differently on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

CPython's C-level calls may bypass Python overrides. PyPy may go
through them. Test explicitly on both runtimes.

---

### PPY013 — sys.getsizeof() raises TypeError on PyPy

**Severity:** Error | **Affects:** PyPy all versions

PyPy deliberately raises `TypeError`. Use vmprof for memory profiling.

---

### PPY014 — String concatenation in loops is O(n²) on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
result = ''.join(items)
```

---

### PPY015 — Generator cleanup timing differs on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
gen.close()   # always close generators explicitly
```

---

### PPY016 — Instance __dict__ ordering not guaranteed on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

PyPy uses hidden classes — instance `__dict__` order may not match CPython.

---

### PPY017 — Adding __del__ to existing class not called on PyPy

**Severity:** Error | **Affects:** PyPy all versions

`MyClass.__del__ = fn` after class definition will NOT be called on PyPy.

---

### PPY018 — sys.setrecursionlimit() behaviour differs on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

Sets stack space to `n * 768` bytes, not exact depth. Actual depth ≈ n/5.

---

### PPY019 — float('nan') identity differs between CPython and PyPy

**Severity:** Warning | **Affects:** PyPy all versions

On PyPy, `float('nan') is float('nan')` is `True`. On CPython it is `False`.
Sets cannot contain multiple NaNs on PyPy.

---

### PPY020 — dict(**kwargs) requires string keys on PyPy and Python 3

**Severity:** Error | **Affects:** PyPy all versions

Non-string keys raise `TypeError`.

---

### PPY021 — Socket not closed promptly on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
with socket.socket() as s:
    ...
```

---

### PPY022 — PYTHONHASHSEED=0 has no effect on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

PyPy always uses hash randomisation regardless of `PYTHONHASHSEED`.

---

### PPY023 — inspect.ismethod() returns different results on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

Built-in method wrappers return `True` on PyPy, `False` on CPython.

---

### PPY024 — timeit reports average not minimum on PyPy

**Severity:** Info | **Affects:** PyPy all versions

JIT warmup makes minimum misleading. PyPy reports average and std dev.

---

### PPY025 — Set iteration order differs between CPython and PyPy

**Severity:** Warning | **Affects:** PyPy all versions

CPython sets are unordered. PyPy sets are insertion-ordered.

```python
# Good
sorted(my_set)   # deterministic on both runtimes
```

---

### PPY026 — __builtins__ is always a module on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
import builtins
builtins.print = my_print
```

---

### PPY027 — Deleting module/class attributes is slower on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

Set to `None` instead of deleting in hot paths.

---

### PPY028 — readline.parse_and_bind() silently ignored on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

PyPy's readline is not GNU readline. Keybinding calls are silently ignored.

---

### PPY029 — Assigning to __builtins__ has no effect on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
import builtins
builtins.print = my_print
```

---

### PPY030 — sys.flags values may differ between CPython and PyPy

**Severity:** Warning | **Affects:** PyPy all versions

`sys.flags.hash_randomization` is always 1 on PyPy.

---

### PPY031 — Integer 'is' identity semantics differ on PyPy

**Severity:** Info | **Affects:** PyPy all versions

All integers unique by value on PyPy. `x + 1 is x + 1` is always `True`.

```python
# Good
x == y   # not: x is y
```

---

### PPY032 — Mutating dict keys raises RuntimeError on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

On CPython this silently corrupts the dict. On PyPy it raises `RuntimeError`.

---

### PPY033 — Exceptions in __del__ appear at unpredictable times on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
def __del__(self):
    try:
        self.cleanup()
    except Exception:
        pass
```

---

### PPY034 — hash() values may differ between CPython and PyPy

**Severity:** Info | **Affects:** PyPy all versions

Never store hash values persistently or compare across runtimes.

---

### PPY035 — C extension packages may not work correctly on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

`numpy`, `pandas`, `scipy`, `torch`, `psycopg2` and others may crash or
produce wrong results. Check https://pypy.org/compat.html

---

### PPY036 — open() line buffering behaves differently on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

`buffering=1` hint may be ignored on PyPy.

---

### PPY037 — os.urandom() source may differ on PyPy

**Severity:** Info | **Affects:** PyPy all versions

```python
# Good
import secrets
secrets.token_bytes(n)
```

---

### PPY038 — decimal module uses different backend on PyPy

**Severity:** Info | **Affects:** PyPy all versions

CPython uses a C implementation. PyPy uses pure Python/RPython — slower
with potential rounding differences in edge cases.

---

### PPY039 — os.fork() may not work correctly on all PyPy platforms

**Severity:** Warning | **Affects:** PyPy all versions

JIT state may not reset correctly in child process.

```python
# Good
multiprocessing.set_start_method('spawn')
```

---

### PPY040 — subprocess.PIPE buffering may cause deadlocks on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

```python
# Good
stdout, stderr = proc.communicate()
```

---

### PPY041 — dict | operator requires PyPy 7.3.7+

**Severity:** Info | **Affects:** PyPy < 7.3.7

```python
# Good for older PyPy
{**d1, **d2}
```

---

### PPY042 — print(flush=True) may not flush immediately on PyPy

**Severity:** Info | **Affects:** PyPy all versions

```python
# Good
sys.stdout.flush()
```

---

### PPY043 — __slots__ memory savings differ on PyPy

**Severity:** Info | **Affects:** PyPy all versions

`__slots__` works correctly on PyPy but memory savings differ from CPython.
Measure independently on each runtime.

---

### PPY044 — Exception variable cleanup timing differs on PyPy

**Severity:** Info | **Affects:** PyPy all versions

```python
# Good — save before except block exits
except Exception as e:
    saved_exc = e
```

---

### PPY045 — sys.settrace() disables JIT on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

Disables PyPy's JIT entirely — 10-100x performance degradation.
Use vmprof for profiling on PyPy.

---

## Adding your own rules

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the complete guide.

Rule IDs `CPY046+` and `PPY046+` are open for community contributions.