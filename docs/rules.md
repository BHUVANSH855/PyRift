# pyrift — Rule Reference

Complete documentation for all pyrift rules.

---

## CPython rules

These rules detect code that behaves differently across CPython versions.

---

### CPY001 — Dict ordering assumption

**Severity:** Warning
**Affects:** CPython < 3.7, PyPy < 7.3

#### What it detects

Code that compares `dict.keys()`, `dict.values()`, or `dict.items()` directly
to an ordered sequence (list or tuple), implicitly assuming insertion order.

#### Why it matters

Dict insertion order is only guaranteed from CPython 3.7+ and PyPy 7.3+.
On older runtimes, this comparison silently returns `False` even when the
contents are identical — a wrong result with no error raised.

#### Example

```python
# Bad — assumes dict is ordered
d = {'a': 1, 'b': 2}
assert d.keys() == ['a', 'b']  # may silently fail on older runtimes

# Good — order-independent comparison
assert set(d.keys()) == {'a', 'b'}
```

---

### CPY002 — Exception.add_note() requires Python 3.11+

**Severity:** Error
**Affects:** CPython ≤ 3.10

#### What it detects

Calls to `exception.add_note()` introduced in PEP 678 (Python 3.11).

#### Why it matters

On Python 3.10 and below, calling `add_note()` raises `AttributeError`
at runtime — crashing the except block that was meant to handle the error.

#### Example

```python
# Bad
try:
    connect()
except ConnectionError as e:
    e.add_note("Check your network settings")  # AttributeError on 3.10
    raise

# Good
try:
    connect()
except ConnectionError as e:
    if sys.version_info >= (3, 11):
        e.add_note("Check your network settings")
    raise
```

---

### CPY003 — X | Y union type syntax requires Python 3.10+

**Severity:** Error
**Affects:** CPython ≤ 3.9

#### What it detects

Use of `X | Y` as a runtime type expression inside `isinstance()` or
`issubclass()` — introduced in PEP 604 (Python 3.10).

#### Why it matters

On Python 3.9 and below, `isinstance(x, int | str)` raises `TypeError`
at runtime. This is distinct from using `X | Y` in type annotations,
which is handled by `from __future__ import annotations`.

#### Example

```python
# Bad — raises TypeError on 3.9
if isinstance(value, int | str):
    process(value)

# Good — works on all Python 3 versions
if isinstance(value, (int, str)):
    process(value)
```

---

### CPY004 — tomllib requires Python 3.11+

**Severity:** Error
**Affects:** CPython ≤ 3.10

#### What it detects

Direct import of `tomllib` from the standard library (added in PEP 680,
Python 3.11).

#### Example

```python
# Bad — ModuleNotFoundError on 3.10
import tomllib

# Good — with fallback
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # pip install tomli
```

---

### CPY005 — match/case requires Python 3.10+

**Severity:** Error
**Affects:** CPython ≤ 3.9

#### What it detects

Use of structural pattern matching (`match`/`case`) introduced in PEP 634
(Python 3.10).

#### Why it matters

On Python 3.9 and below, `match` statements are a `SyntaxError` — the
entire module fails to import, not just the code path that uses `match`.

#### Example

```python
# Bad — SyntaxError on 3.9, entire file fails to import
match command:
    case "quit":
        sys.exit()

# Good
if command == "quit":
    sys.exit()
```

---

### CPY006 — asyncio.timeout() / TaskGroup requires Python 3.11+

**Severity:** Error
**Affects:** CPython ≤ 3.10

#### What it detects

Use of `asyncio.timeout()`, `asyncio.timeout_at()`, or `asyncio.TaskGroup`
— all added in Python 3.11.

#### Example

```python
# Bad — AttributeError on 3.10
async with asyncio.timeout(5.0):
    await fetch_data()

# Good
await asyncio.wait_for(fetch_data(), timeout=5.0)
```

---

### CPY007 — Module removed in Python 3.13

**Severity:** Error
**Affects:** CPython ≥ 3.13

#### What it detects

Import of any of the 21 modules removed from the standard library in
Python 3.13 per PEP 594.

#### Removed modules

`aifc`, `audioop`, `cgi`, `cgitb`, `chunk`, `crypt`, `imghdr`,
`mailcap`, `msilib`, `nis`, `nntplib`, `ossaudiodev`, `pipes`,
`sndhdr`, `spwd`, `sunau`, `telnetlib`, `uu`, `xdrlib`,
`asynchat`, `asyncore`, `smtpd`

---

## PyPy rules

These rules detect code that behaves differently on PyPy vs CPython.

---

### PPY001 — Relying on __del__ for resource cleanup

**Severity:** Error
**Affects:** PyPy all versions

#### What it detects

`__del__` methods that call resource-cleanup methods such as `close()`,
`flush()`, `release()`, `shutdown()`, or `disconnect()`.

#### Why it matters

CPython uses reference counting — `__del__` is called immediately when
the last reference drops. PyPy uses a tracing GC — `__del__` may be
called much later or never, silently leaking file handles, sockets,
database connections, and locks.

#### Example

```python
# Bad — leaks resources on PyPy
class DatabaseConnection:
    def __del__(self):
        self.conn.close()  # may never be called on PyPy

# Good — guaranteed cleanup on all runtimes
class DatabaseConnection:
    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

# Usage
with DatabaseConnection() as db:
    db.query("SELECT 1")
```

---

### PPY002 — ctypes usage may silently fail on PyPy

**Severity:** Warning
**Affects:** PyPy all versions

#### What it detects

Use of dangerous `ctypes` members: `CDLL`, `WinDLL`, `CFUNCTYPE`,
`cast`, `pointer`, `byref`, `Structure`, `Union`, and others.

#### Why it matters

PyPy's ctypes implementation is incomplete. Pointer arithmetic, callbacks,
and bit-field structures may silently produce wrong results or segfault
on PyPy while working correctly on CPython.

#### Suggestion

Use `cffi` instead — it is fully supported on both CPython and PyPy.

---

### PPY003 — sys.getrefcount() is meaningless on PyPy

**Severity:** Error
**Affects:** PyPy all versions

#### What it detects

Calls to `sys.getrefcount()`.

#### Why it matters

`sys.getrefcount()` relies on CPython's reference-counting GC. PyPy uses
a tracing GC with no reference counting — `sys.getrefcount()` always
returns a dummy constant value on PyPy (typically 0 or 65536). Any logic
based on this value silently produces wrong results.

#### Example

```python
# Bad — always wrong on PyPy
if sys.getrefcount(obj) == 1:
    cleanup(obj)

# Good — use gc.get_referrers() instead
import gc
if len(gc.get_referrers(obj)) == 1:
    cleanup(obj)
```

---

### PPY004 — weakref.proxy() raises ReferenceError unpredictably on PyPy

**Severity:** Warning
**Affects:** PyPy all versions

#### What it detects

Calls to `weakref.proxy()`.

#### Why it matters

On CPython, `weakref.proxy()` raises `ReferenceError` only when the
proxied object is accessed after it has been collected. On PyPy, due to
GC differences, `ReferenceError` may be raised at unpredictable points —
even before the object appears dead from CPython's perspective.

#### Example

```python
# Bad — ReferenceError timing unpredictable on PyPy
p = weakref.proxy(obj)
do_something()
p.method()  # may raise ReferenceError on PyPy at unexpected times

# Good — explicit null check
ref = weakref.ref(obj)
target = ref()
if target is not None:
    target.method()
```

---

## Adding your own rules

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the complete guide on
writing and submitting new rules.