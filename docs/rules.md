# pyrift — Rule Reference

Complete documentation for all 17 pyrift rules.

---

## CPython rules

These rules detect code that behaves differently across CPython versions.

---

### CPY001 — Dict ordering assumption

**Severity:** Warning | **Affects:** CPython < 3.7, PyPy < 7.3

Dict insertion order is only guaranteed from CPython 3.7+ and PyPy 7.3+.
Comparing `dict.keys()`, `dict.values()`, or `dict.items()` directly to
an ordered sequence silently returns wrong results on older runtimes.

```python
# Bad
assert d.keys() == ['a', 'b']   # may silently fail

# Good
assert set(d.keys()) == {'a', 'b'}
```

---

### CPY002 — Exception.add_note() requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

`Exception.add_note()` was introduced in PEP 678 (Python 3.11).
On 3.10 and below, calling it raises `AttributeError` inside the
except block that was meant to handle the error.

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

Using `X | Y` as a runtime type expression inside `isinstance()` or
`issubclass()` raises `TypeError` on Python 3.9 and below.

```python
# Bad
isinstance(x, int | str)   # TypeError on 3.9

# Good
isinstance(x, (int, str))
```

---

### CPY004 — tomllib requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

`tomllib` was added to the standard library in PEP 680 (Python 3.11).
On 3.10 and below, `import tomllib` raises `ModuleNotFoundError`.

```python
# Bad
import tomllib   # ModuleNotFoundError on 3.10

# Good
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib   # pip install tomli
```

---

### CPY005 — match/case requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9

Structural pattern matching (`match`/`case`) was introduced in PEP 634
(Python 3.10). On 3.9 and below it is a `SyntaxError` — the entire
module fails to import, not just the path using `match`.

```python
# Bad — entire file fails to import on 3.9
match command:
    case "quit": sys.exit()

# Good
if command == "quit":
    sys.exit()
```

---

### CPY006 — asyncio.timeout() / TaskGroup requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

`asyncio.timeout()`, `asyncio.timeout_at()`, and `asyncio.TaskGroup`
were all added in Python 3.11. On 3.10, they raise `AttributeError`.

```python
# Bad
async with asyncio.timeout(5.0):   # AttributeError on 3.10
    await fetch()

# Good
await asyncio.wait_for(fetch(), timeout=5.0)
```

---

### CPY007 — Module removed in Python 3.13

**Severity:** Error | **Affects:** CPython ≥ 3.13

PEP 594 removed 21 legacy modules from the standard library in Python 3.13.
Importing them raises `ModuleNotFoundError`.

**Removed modules:** `aifc`, `audioop`, `cgi`, `cgitb`, `chunk`, `crypt`,
`imghdr`, `mailcap`, `msilib`, `nis`, `nntplib`, `ossaudiodev`, `pipes`,
`sndhdr`, `spwd`, `sunau`, `telnetlib`, `uu`, `xdrlib`, `asynchat`,
`asyncore`, `smtpd`

---

### CPY008 — __slots__ may not prevent __dict__ with base classes

**Severity:** Info | **Affects:** CPython all versions

When a class defines `__slots__` but inherits from a class that has
`__dict__`, the subclass will also have `__dict__` — `__slots__` does
not prevent it. This is a commonly misunderstood behaviour.

```python
# Risky — Child still has __dict__ because Base does
class Base: pass
class Child(Base):
    __slots__ = ['x']   # does NOT prevent __dict__

# Safe — all classes in hierarchy define __slots__
class Base:
    __slots__ = ()
class Child(Base):
    __slots__ = ['x']
```

---

### CPY009 — ExceptionGroup requires Python 3.11+

**Severity:** Error | **Affects:** CPython ≤ 3.10

`ExceptionGroup` and `BaseExceptionGroup` are built-ins added in
PEP 654 (Python 3.11). On 3.10 and below they raise `NameError`.

```python
# Bad — NameError on 3.10
raise ExceptionGroup("errors", [e1, e2])

# Good
try:
    import exceptiongroup   # pip install exceptiongroup
except ImportError:
    pass   # guard for 3.11+
```

---

### CPY010 — @dataclass(slots=True) requires Python 3.10+

**Severity:** Error | **Affects:** CPython ≤ 3.9

The `slots` parameter for `@dataclass` was added in Python 3.10.
On 3.9 and below, `@dataclass(slots=True)` raises `TypeError` at
class definition time — before any instance is created.

```python
# Bad — TypeError on 3.9
@dataclass(slots=True)
class Point:
    x: float

# Good for 3.9 compatibility
@dataclass
class Point:
    __slots__ = ('x', 'y')
    x: float
    y: float
```

---

## PyPy rules

These rules detect code that behaves differently on PyPy vs CPython.

---

### PPY001 — Relying on __del__ for resource cleanup

**Severity:** Error | **Affects:** PyPy all versions

CPython uses reference counting — `__del__` is called immediately when
the last reference drops. PyPy uses a tracing GC — `__del__` may be
called much later or never, silently leaking file handles, sockets,
locks, and database connections.

```python
# Bad — leaks on PyPy
class Conn:
    def __del__(self):
        self.socket.close()   # may never run on PyPy

# Good — guaranteed on all runtimes
class Conn:
    def __enter__(self): return self
    def __exit__(self, *a): self.socket.close()

with Conn() as c:
    c.query()
```

---

### PPY002 — ctypes usage may silently fail on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

PyPy's ctypes implementation is incomplete. Pointer arithmetic, callbacks,
and bit-field structures may silently produce wrong results or segfault
on PyPy while working on CPython.

**Suggestion:** Use `cffi` — fully supported on both CPython and PyPy.

---

### PPY003 — sys.getrefcount() is meaningless on PyPy

**Severity:** Error | **Affects:** PyPy all versions

`sys.getrefcount()` relies on CPython's reference-counting GC. PyPy
uses a tracing GC — `sys.getrefcount()` always returns a dummy constant
(typically 0 or 65536). Any logic based on this value silently produces
wrong results on PyPy.

```python
# Bad — always wrong on PyPy
if sys.getrefcount(obj) == 1:
    cleanup(obj)

# Good
import gc
if len(gc.get_referrers(obj)) == 1:
    cleanup(obj)
```

---

### PPY004 — weakref.proxy() raises ReferenceError unpredictably on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

On CPython, `weakref.proxy()` raises `ReferenceError` only when the
proxied object is accessed after collection. On PyPy, `ReferenceError`
may be raised at unpredictable points due to GC timing differences.

```python
# Bad
p = weakref.proxy(obj)

# Good — explicit null check
ref = weakref.ref(obj)
target = ref()
if target is not None:
    target.method()
```

---

### PPY005 — File write without explicit flush may lose data on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

On PyPy, file buffering behaviour differs from CPython due to GC timing.
Data written to files may not be flushed to disk even after `close()`,
silently losing writes.

```python
# Bad — may lose data on PyPy
f = open('out.txt', 'w')
f.write(data)
f.close()

# Good — context manager guarantees flush + close
with open('out.txt', 'w') as f:
    f.write(data)
```

---

### PPY006 — Monkey-patching built-in types behaves differently on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

PyPy's JIT makes aggressive assumptions about built-in types. Patching
them may silently produce wrong results or bypass JIT optimisations
without raising any error.

```python
# Bad
list.custom = lambda self: None

# Good — subclass instead
class MyList(list):
    def custom(self):
        pass
```

---

### PPY007 — sys.intern() identity guarantees differ on PyPy

**Severity:** Warning | **Affects:** PyPy all versions

On CPython, interned strings are guaranteed to share identity — `is`
returns `True` for equal interned strings. On PyPy, the JIT may not
preserve this identity guarantee.

```python
# Bad — identity not guaranteed on PyPy
a = sys.intern('hello')
b = sys.intern('hello')
assert a is b   # may fail on PyPy

# Good — always use == for string equality
assert a == b
```

---

## Adding your own rules

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the complete guide on
writing and submitting new rules. Rule IDs `CPY011+` and `PPY008+`
are available for community contributions.