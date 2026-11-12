# pyrift — Rule Reference

Complete documentation for all 119 pyrift rules.

---

## How to read a finding

A pyrift finding tells you:

1. **What triggered it** — the rule ID and title (e.g. `CPY033 pathlib.Path.is_relative_to() requires Python 3.9+`)
2. **How serious it is** — the severity level
3. **How confident pyrift is** — the confidence level
4. **Which runtimes are affected** — CPython, PyPy, or both
5. **Which version range is affected** — the `Affected versions` field

### Severity levels

| Severity | Meaning | Recommended action |
|---|---|---|
| `ERROR` | Silent wrong behaviour — crash or data corruption on the affected version | Fix before shipping |
| `WARNING` | Different behaviour — may or may not matter depending on your use case | Review and decide |
| `INFO` | Worth knowing — low urgency, cosmetic or future-proofing concern | Fix when convenient |

### Confidence levels

| Confidence | Meaning |
|---|---|
| `HIGH` | Backed by official Python/PyPy docs or confirmed runtime probe |
| `MEDIUM` | Strongly implied by docs or related behaviour |
| `LOW` | Observed in practice — not formally documented |

Rules with `LOW` confidence are still included because the behaviour is real,
but you should verify independently before acting on them.

---

## What to do with a finding

The general pattern for fixing a pyrift finding is:

1. **Understand the version range** — check `Affected versions`. If your project's minimum supported Python
   version is already higher than the affected range, the finding does not apply; add the version floor to
   your `pyproject.toml` so pyrift can skip it automatically:

   ```toml
   [tool.pyrift]
   minimum-python = "3.11"
   ```

2. **Apply the suggested fix** — each finding includes a `suggestion` field in the scan output. The fix is
   almost always one of:
   - Use a newer API that exists on all supported versions
   - Guard the call with a `sys.version_info` check
   - Add a compatibility shim (e.g. `tomli` for `tomllib`, `importlib_resources` for `importlib.resources`)

3. **Suppress if intentional** — if you have deliberately decided to accept the incompatibility, add an
   inline suppression so the finding does not recur:

   ```python
   result = path.is_relative_to(base)  # pyrift: ignore[CPY033]
   ```

   Or suppress all rules on a line:

   ```python
   some_code()  # pyrift: ignore
   ```

4. **Per-directory overrides** — for test directories or vendored code where different rules apply, use
   `[[tool.pyrift.per-path]]` in `pyproject.toml`:

   ```toml
   [[tool.pyrift.per-path]]
   path = "tests/**/*.py"
   ignore = ["CPY033", "CPY034"]
   ```

---

## Programmatic access

```python
import pyrift

# Scan a directory
result = pyrift.scan(".")
print(result.breakdown())
# {"high_confidence": 2, "medium_confidence": 0, "informational": 0, "analyzer_errors": 0}

# Scan a source string
findings = pyrift.scan_source("""
import pathlib
p = pathlib.Path("/a")
p.is_relative_to("/b")
""")
for f in findings:
    print(f.rule_id, f.line, f.title)
```

---

## CPython rules — version compatibility

These rules detect code that behaves differently across CPython versions.

### CPY001 — Dict ordering assumption — comparing dict view to ordered sequence

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.7`

**References:** [What's New 3.7](https://docs.python.org/3/whatsnew/3.7.html#summary-release-highlights) · [cpython #33609](https://github.com/python/cpython/issues/33609)

**Contract:** Documented | **Basis:** Documented

---
### CPY002 — Exception.add_note() requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-678-exceptions-can-be-enriched-with-notes) · [cpython #89770](https://github.com/python/cpython/issues/89770)

**Contract:** Documented | **Basis:** Documented

---
### CPY003 — X | Y union type syntax requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#pep-604-new-type-union-operator) · [cpython #41428](https://github.com/python/cpython/issues/41428)

**Contract:** Documented | **Basis:** Documented

---
### CPY004 — tomllib requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#whatsnew311-new-modules) · [cpython #40059](https://github.com/python/cpython/issues/40059)

**Contract:** Documented | **Basis:** Documented

---
### CPY005 — match/case requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#pep-634-structural-pattern-matching) · [cpython #86294](https://github.com/python/cpython/issues/86294)

**Contract:** Documented | **Basis:** Documented

---
### CPY006 — asyncio.timeout() / TaskGroup requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#asyncio) · [cpython #90927](https://github.com/python/cpython/issues/90927)

**Contract:** Documented | **Basis:** Documented

---
### CPY007 — Module removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#pep-594-remove-dead-batteries-from-the-standard-library) · [cpython #42611](https://github.com/python/cpython/issues/42611)

**Contract:** Removed | **Basis:** Documented

---
### CPY008 — __slots__ may not prevent __dict__ on Python < 3.10

**Severity:** Info | **Confidence:** Medium | **Runtime:** CPython

**Affected versions:** `<3.10`

**Contract:** Documented | **Basis:** Documented

---
### CPY009 — ExceptionGroup requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-654-exception-groups-and-except) · [cpython #45292](https://github.com/python/cpython/issues/45292)

**Contract:** Documented | **Basis:** Documented

---
### CPY010 — @dataclass(slots=True) requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#dataclasses) · [cpython #45171](https://github.com/python/cpython/issues/45171)

**Contract:** Documented | **Basis:** Documented

---
### CPY011 — typing.Self requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-673-self-type) · [cpython #46534](https://github.com/python/cpython/issues/46534)

**Contract:** Documented | **Basis:** Documented

---
### CPY012 — typing.LiteralString requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-675-arbitrary-literal-string-type) · [cpython #47088](https://github.com/python/cpython/issues/47088)

**Contract:** Documented | **Basis:** Documented

---
### CPY013 — typing.override requires Python 3.12+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#pep-698-override-decorator-for-static-typing) · [cpython #101561](https://github.com/python/cpython/issues/101561)

**Contract:** Documented | **Basis:** Documented

---
### CPY014 — typing.TypeAlias requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#pep-613-typealias) · [cpython #41370](https://github.com/python/cpython/issues/41370)

**Contract:** Documented | **Basis:** Documented

---
### CPY015 — typing.Never requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#typing) · [cpython #46475](https://github.com/python/cpython/issues/46475)

**Contract:** Documented | **Basis:** Documented

---
### CPY016 — typing.TypeVarTuple requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-646-variadic-generics) · [cpython #43224](https://github.com/python/cpython/issues/43224)

**Contract:** Documented | **Basis:** Documented

---
### CPY017 — typing.Unpack requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-646-variadic-generics) · [cpython #43224](https://github.com/python/cpython/issues/43224)

**Contract:** Documented | **Basis:** Documented

---
### CPY018 — typing.Required / NotRequired requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#pep-655-marking-individual-typeddict-items-as-required-or-not-required) · [cpython #47087](https://github.com/python/cpython/issues/47087)

**Contract:** Documented | **Basis:** Documented

---
### CPY019 — distutils removed from the Python standard library in 3.12+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#removed) · [cpython #92584](https://github.com/python/cpython/issues/92584)

**Contract:** Removed | **Basis:** Documented

---
### CPY020 — datetime.UTC requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#datetime) · [cpython #91928](https://github.com/python/cpython/issues/91928)

**Contract:** Documented | **Basis:** Documented

---
### CPY022 — Bitwise inversion on bool (~True/~False) deprecated in 3.12

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#deprecated) · [cpython #82012](https://github.com/python/cpython/issues/82012)

**Contract:** Deprecated | **Basis:** Deprecation

---
### CPY023 — multiprocessing default start method changing in Python 3.14

**Severity:** Warning | **Confidence:** Medium | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#multiprocessing) · [cpython #84559](https://github.com/python/cpython/issues/84559)

**Contract:** Documented | **Basis:** Documented

---
### CPY024 — typing.TypeGuard requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#pep-647-user-defined-type-guards) · [cpython #43412](https://github.com/python/cpython/issues/43412)

**Contract:** Documented | **Basis:** Documented

---
### CPY025 — typing.ParamSpec requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#pep-612-parameter-specification-variables) · [cpython #41559](https://github.com/python/cpython/issues/41559)

**Contract:** Documented | **Basis:** Documented

---
### CPY026 — typing.io and typing.re removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#typing) · [cpython #92871](https://github.com/python/cpython/issues/92871)

**Contract:** Removed | **Basis:** Documented

---
### CPY027 — locale.resetlocale() removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#locale) · [cpython #104783](https://github.com/python/cpython/issues/104783)

**Contract:** Removed | **Basis:** Deprecation

---
### CPY028 — lib2to3 removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#pep-594-remove-dead-batteries-from-the-standard-library) · [cpython #84540](https://github.com/python/cpython/issues/84540)

**Contract:** Removed | **Basis:** Documented

---
### CPY029 — locals() semantics changed in Python 3.13 (PEP 667)

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#defined-mutation-semantics-for-locals) · [cpython #74929](https://github.com/python/cpython/issues/74929)

**Contract:** Documented | **Basis:** Implementation Defined

---
### CPY030 — sys.path no longer accepts bytes entries in Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#other-language-changes) · [cpython #91181](https://github.com/python/cpython/issues/91181)

**Contract:** Documented | **Basis:** Documented

---
### CPY031 — typing.assert_never requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#typing) · [cpython #46475](https://github.com/python/cpython/issues/46475)

**Contract:** Documented | **Basis:** Documented

---
### CPY032 — typing.reveal_type requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#typing) · [cpython #46414](https://github.com/python/cpython/issues/46414)

**Contract:** Documented | **Basis:** Documented

---
### CPY033 — pathlib.Path.is_relative_to() requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#pathlib) · [cpython #40358](https://github.com/python/cpython/issues/40358)

**Contract:** Documented | **Basis:** Documented

---
### CPY034 — int.bit_count() requires Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#other-language-changes) · [cpython #74068](https://github.com/python/cpython/issues/74068)

**Contract:** Documented | **Basis:** Documented

---
### CPY035 — str.removeprefix/removesuffix requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#pep-616-new-removeprefix-and-removesuffix-string-methods) · [cpython #39939](https://github.com/python/cpython/issues/39939)

**Contract:** Documented | **Basis:** Documented

---
### CPY036 — datetime.utcnow() deprecated since Python 3.12

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#deprecated) · [cpython #103857](https://github.com/python/cpython/issues/103857)

**Contract:** Deprecated | **Basis:** Deprecation

---
### CPY037 — datetime.utcfromtimestamp() deprecated since Python 3.12

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#deprecated) · [cpython #103857](https://github.com/python/cpython/issues/103857)

**Contract:** Deprecated | **Basis:** Deprecation

---
### CPY038 — asyncio.get_event_loop() raises RuntimeError in Python 3.14+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#asyncio) · [cpython #126353](https://github.com/python/cpython/issues/126353)

**Contract:** Documented | **Basis:** Documented

---
### CPY039 — zoneinfo module requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#zoneinfo) · [cpython #40503](https://github.com/python/cpython/issues/40503)

**Contract:** Documented | **Basis:** Documented

---
### CPY040 — graphlib module requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#graphlib) · [cpython #17005](https://github.com/python/cpython/issues/17005)

**Contract:** Documented | **Basis:** Documented

---
### CPY041 — dict | merge operator requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#dictionary-merge-update-operators) · [cpython #36144](https://github.com/python/cpython/issues/36144)

**Contract:** Documented | **Basis:** Documented

---
### CPY042 — aiter() and anext() builtins require Python 3.10+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#other-language-changes) · [cpython #31861](https://github.com/python/cpython/issues/31861)

**Contract:** Documented | **Basis:** Documented

---
### CPY043 — math.lcm() requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#math) · [cpython #39479](https://github.com/python/cpython/issues/39479)

**Contract:** Documented | **Basis:** Documented

---
### CPY044 — math.gcd() with multiple args requires Python 3.9+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.9`

**References:** [What's New 3.9](https://docs.python.org/3/whatsnew/3.9.html#math) · [cpython #39474](https://github.com/python/cpython/issues/39474)

**Contract:** Documented | **Basis:** Documented

---
### CPY045 — NaN hash behaviour changed in Python 3.10

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#other-language-changes) · [cpython #43475](https://github.com/python/cpython/issues/43475)

**Contract:** Documented | **Basis:** Documented

---
### CPY046 — open() without encoding= uses platform-dependent encoding before 3.15

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `<=3.14`

**References:** [What's New 3.15](https://docs.python.org/3/whatsnew/3.15.html#whatsnew315-utf8-default) · [cpython #133711](https://github.com/python/cpython/issues/133711)

**Contract:** Documented | **Basis:** Documented

---
### CPY047 — collections.abc.ByteString deprecated, scheduled removal in Python 3.17

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12,<3.17`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#deprecated) · [cpython #91896](https://github.com/python/cpython/issues/91896)

**Contract:** Deprecated | **Basis:** Documented

---
### CPY048 — concurrent.interpreters requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pep-734-multiple-interpreters-in-the-standard-library) · [cpython #134939](https://github.com/python/cpython/issues/134939)

**Contract:** Documented | **Basis:** Documented

---
### CPY049 — compression.zstd requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pep-784-zstandard-support-in-the-standard-library) · [cpython #132983](https://github.com/python/cpython/issues/132983)

**Contract:** Documented | **Basis:** Documented

---
### CPY050 — PurePath.is_reserved() deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13,<3.15`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#pathlib) · [cpython #88569](https://github.com/python/cpython/issues/88569)

**Contract:** Removed | **Basis:** Deprecation

---
### CPY051 — Module-level mutable state may require synchronization in free-threaded Python

**Severity:** Warning | **Confidence:** Medium | **Runtime:** CPython

**Affected versions:** `>=3.13`

**Contract:** Implementation Defined | **Basis:** Documented

---
### CPY053 — typing.get_overloads() requires Python 3.11+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.11`

**References:** [What's New 3.11](https://docs.python.org/3/whatsnew/3.11.html#typing) · [cpython #89263](https://github.com/python/cpython/issues/89263)

**Contract:** Documented | **Basis:** Documented

---
### CPY054 — int() no longer delegates to __trunc__() in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#built-ins) · [cpython #119743](https://github.com/python/cpython/issues/119743)

**Contract:** Documented | **Basis:** Documented

---
### CPY055 — NotImplemented in boolean context raises TypeError in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#changes-in-python-behavior) · [cpython #116023](https://github.com/python/cpython/issues/116023)

**Contract:** Documented | **Basis:** Documented

---
### CPY057 — pickle default protocol changed to 5 in Python 3.14

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pickle) · [cpython #118830](https://github.com/python/cpython/issues/118830)

**Contract:** Documented | **Basis:** Documented

---
### CPY062 — string.templatelib requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pep-750-template-string-literals) · [cpython #132661](https://github.com/python/cpython/issues/132661)

**Contract:** Documented | **Basis:** Documented

---
### CPY063 — annotationlib requires Python 3.14+

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pep-649-pep-749-deferred-evaluation-of-annotations) · [cpython #119180](https://github.com/python/cpython/issues/119180)

**Contract:** Documented | **Basis:** Documented

---
### CPY064 — Deprecated AST node types removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#ast) · [cpython #119562](https://github.com/python/cpython/issues/119562)

**Contract:** Removed | **Basis:** Documented

---
### CPY065 — pkgutil.find_loader()/get_loader() removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pkgutil) · [cpython #97850](https://github.com/python/cpython/issues/97850)

**Contract:** Removed | **Basis:** Documented

---
### CPY066 — asyncio child watcher classes removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#asyncio) · [cpython #94597](https://github.com/python/cpython/issues/94597)

**Contract:** Removed | **Basis:** Documented

---
### CPY067 — typing.NamedTuple keyword syntax removed in Python 3.15

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13,<3.15`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#typing) · [cpython #105566](https://github.com/python/cpython/issues/105566)

**Contract:** Removed | **Basis:** Deprecation

---
### CPY068 — typing.no_type_check_decorator deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13,<3.15`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#typing) · [cpython #106309](https://github.com/python/cpython/issues/106309)

**Contract:** Removed | **Basis:** Deprecation

---
### CPY069 — asyncio.iscoroutinefunction() deprecated in Python 3.14

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#asyncio) · [cpython #122858](https://github.com/python/cpython/issues/122858)

**Contract:** Deprecated | **Basis:** Deprecation

---
### CPY070 — asyncio event loop policy deprecated in Python 3.14

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#asyncio) · [cpython #127949](https://github.com/python/cpython/issues/127949)

**Contract:** Deprecated | **Basis:** Deprecation

---
### CPY071 — pty.master_open()/slave_open() removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#pty) · [cpython #118824](https://github.com/python/cpython/issues/118824)

**Contract:** Removed | **Basis:** Documented

---
### CPY072 — importlib.abc resource classes removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#importlib-abc) · [cpython #93963](https://github.com/python/cpython/issues/93963)

**Contract:** Removed | **Basis:** Documented

---
### CPY073 — sqlite3.version/version_info removed in Python 3.14

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#sqlite3) · [cpython #118924](https://github.com/python/cpython/issues/118924)

**Contract:** Removed | **Basis:** Documented

---
### CPY074 — code.__lnotab__ deprecated since Python 3.10 (PEP 626)

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.10`

**References:** [What's New 3.10](https://docs.python.org/3/whatsnew/3.10.html#pep-626-precise-line-numbers-for-debugging-and-other-tools) · [cpython #33418](https://github.com/python/cpython/issues/33418)

**Contract:** Deprecated | **Basis:** Documented

---
### CPY075 — http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13,<3.15`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#http-server) · [cpython #109096](https://github.com/python/cpython/issues/109096)

**Contract:** Removed | **Basis:** Deprecation

---
### CPY076 — ssl.wrap_socket() removed in Python 3.12

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.12`

**References:** [What's New 3.12](https://docs.python.org/3/whatsnew/3.12.html#removed) · [cpython #94199](https://github.com/python/cpython/issues/94199)

**Contract:** Removed | **Basis:** Documented

---
### CPY077 — typing.TypedDict zero-field syntax removed in Python 3.15

**Severity:** Error | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.13,<3.15`

**References:** [What's New 3.13](https://docs.python.org/3/whatsnew/3.13.html#typing) · [cpython #105570](https://github.com/python/cpython/issues/105570)

**Contract:** Removed | **Basis:** Deprecation

---
### CPY078 — functools.reduce() keyword arguments deprecated, removal scheduled for 3.16

**Severity:** Warning | **Confidence:** High | **Runtime:** CPython

**Affected versions:** `>=3.14,<3.16`

**References:** [What's New 3.14](https://docs.python.org/3/whatsnew/3.14.html#new-deprecations) · [cpython #121676](https://github.com/python/cpython/issues/121676)

**Contract:** Deprecated | **Basis:** Documented

---

---

## PyPy rules — runtime compatibility

These rules detect code that behaves differently on PyPy vs CPython.

### PPY001 — Relying on __del__ for resource cleanup breaks on PyPy

**Severity:** Error | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY002 — ctypes usage may differ on PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY003 — sys.getrefcount() is meaningless on PyPy

**Severity:** Error | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY004 — weakref.proxy() lifetime differs on PyPy due to GC model

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY005 — File write without explicit lifecycle management on PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY006 — Monkey-patching built-in types behaves differently on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY007 — sys.intern() identity guarantees differ on PyPy

**Severity:** Info | **Confidence:** Low | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Observed

---
### PPY008 — threading.local() cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY009 — id() stability depends on PyPy GC configuration

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY010 — gc.collect() behaviour differs on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY012 — Overriding built-in methods may behave differently on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY013 — sys.getsizeof() raises TypeError on PyPy

**Severity:** Error | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY014 — String concatenation in loop is O(n²) on PyPy

**Severity:** Info | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY015 — Generator cleanup timing differs on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY016 — Instance __dict__ order-sensitive access may differ on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY017 — Adding __del__ to existing class not called on PyPy

**Severity:** Error | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY018 — sys.setrecursionlimit() behaviour differs on PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY019 — float('nan') identity differs between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY021 — Socket not closed promptly on PyPy — GC timing

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY022 — Hash values for the same input differ between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY023 — inspect.ismethod() returns different results on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY024 — timeit reports average not minimum on PyPy

**Severity:** Info | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY025 — Set iteration order differs between CPython and PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY026 — __builtins__ is always a module on PyPy, never a dict

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY027 — Deleting module/class attributes may be slower on PyPy

**Severity:** Info | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY028 — readline.parse_and_bind() silently ignored on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY029 — Assigning to __builtins__ has no effect on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY030 — sys.flags values may differ between CPython and PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY031 — Integer 'is' identity semantics differ on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY032 — Mutating dict keys raises RuntimeError on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY033 — Exceptions in __del__ appear at unpredictable times on PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Inferred

---
### PPY034 — hash() values may differ between CPython and PyPy

**Severity:** Info | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY035 — C extension package may need PyPy compatibility verification

**Severity:** Info | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY036 — open() line buffering behaves differently on PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY037 — os.urandom() source may differ on PyPy

**Severity:** Info | **Confidence:** Low | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Observed

---
### PPY038 — decimal module uses different backend on PyPy

**Severity:** Info | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY039 — os.fork() may not work correctly on all PyPy platforms

**Severity:** Warning | **Confidence:** Low | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Observed

---
### PPY040 — subprocess Popen(...PIPE) without communicate() risks deadlock

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY041 — dict | operator requires PyPy 7.3.7+ (Python 3.9 compat)

**Severity:** Info | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3.7`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY042 — print(flush=True) may not flush immediately on PyPy

**Severity:** Info | **Confidence:** Low | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Observed

---
### PPY044 — Exception variable cleanup timing differs on PyPy

**Severity:** Info | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Inferred

---
### PPY045 — sys.settrace() disables JIT and is unreliable on PyPy

**Severity:** Warning | **Confidence:** High | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY047 — ctypes.util.find_library() unreliable on PyPy

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY049 — GC behavior differs between PyPy and CPython

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
### PPY051 — code.__lnotab__ deprecated on PyPy too

**Severity:** Warning | **Confidence:** Medium | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3.11`

**Contract:** Implementation Defined | **Basis:** Observed

---
### PPY052 — importlib.abc resource classes may differ on PyPy

**Severity:** Info | **Confidence:** Low | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Observed

---
### PPY053 — functools.lru_cache thread safety differs on PyPy

**Severity:** Info | **Confidence:** Low | **Runtime:** PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Observed

---

---

## Cross-runtime rules — CPython & PyPy

These rules apply to both CPython and PyPy.

### PPY011 — array.array('u') type code removed in Python 3.13

**Severity:** Error | **Confidence:** High | **Runtime:** CPython & PyPy

**Affected versions:** `>=pypy7.3`

**Contract:** Implementation Defined | **Basis:** Documented

---
