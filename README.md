# PyRift

**Detect silent Python behavior differences before they become bugs.**

PyRift is a Python static-analysis tool for finding code patterns whose behavior, compatibility, or performance can differ across **CPython versions** or between **CPython and PyPy**.

It combines AST-based rules with evidence from Python documentation, PEPs, deprecation/removal notes, implementation-specific documentation, and runtime verification where available. Each finding reports its **runtime target, severity, confidence, evidence type, and intent basis** rather than pretending that every behavior difference is automatically a bug.

[![Tests](https://github.com/BHUVANSH855/PyRift/actions/workflows/tests.yml/badge.svg)](https://github.com/BHUVANSH855/PyRift/actions/workflows/tests.yml)
[![Security](https://github.com/BHUVANSH855/PyRift/actions/workflows/security.yml/badge.svg)](https://github.com/BHUVANSH855/PyRift/actions/workflows/security.yml)
[![Code Scanning](https://github.com/BHUVANSH855/PyRift/actions/workflows/code-scanning.yml/badge.svg)](https://github.com/BHUVANSH855/PyRift/actions/workflows/code-scanning.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Status:** Active development. PyRift is intended for compatibility investigation and review, not as a replacement for running your test suite on the Python runtimes you support.

---

## Why PyRift?

Python compatibility failures are not always obvious.

A program can continue to parse and run while a small runtime or standard-library behavior has changed underneath it. These differences can appear after a Python upgrade, when supporting multiple CPython releases, or when code is expected to work on both CPython and PyPy.

PyRift tries to surface these cases early.

It is designed around a simple workflow:

```text
Python source
     │
     ▼
   AST scan
     │
     ▼
Compatibility rules
     │
     ├── CPython-version differences
     └── CPython ↔ PyPy differences
     │
     ▼
Evidence + metadata
     │
     ├── Documentation
     ├── PEPs
     ├── Deprecation/removal notes
     ├── Runtime verification
     └── Implementation-specific evidence
     │
     ▼
Actionable finding
```

PyRift does **not** try to decide that a behavior change is "intentional" by guessing developer intent. Instead, rules attach evidence and classify what supports the finding. This makes the result reviewable.

---

## What PyRift Finds

PyRift currently contains compatibility rules covering areas such as:

- CPython version-specific deprecations and removals
- AST and syntax changes
- standard-library API changes
- `asyncio` behavior changes
- `typing` compatibility changes
- `sqlite3` version/API changes
- `ssl` and networking APIs
- `http.server` and CGI-related changes
- `pty` behavior
- `pkgutil` behavior
- PyPy-specific runtime and performance differences
- implementation-specific semantics documented by PyPy
- other reviewed compatibility patterns

The repository contains the complete rule catalog in [`docs/rules.md`](docs/rules.md).

Evidence methodology is documented in [`docs/behavior-evidence.md`](docs/behavior-evidence.md).

---

## Installation

### From a local checkout

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/BHUVANSH855/PyRift.git
cd PyRift

python -m venv .venv
```

Activate it:

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

Install PyRift in editable mode:

```bash
python -m pip install -e .
```

Verify the installation:

```bash
pyrift --version
```

### Python environment

PyRift is developed and tested against modern Python versions. Use a supported Python installation and a virtual environment for development.

---

## Quick Start

Scan the current directory:

```bash
pyrift scan .
```

Scan a project:

```bash
pyrift scan path/to/project
```

Write JSON results:

```bash
pyrift scan path/to/project --format json --output pyrift-scan.json
```

Write SARIF results:

```bash
pyrift scan path/to/project --format sarif --output pyrift.sarif
```

Write Markdown results:

```bash
pyrift scan path/to/project --format markdown --output pyrift-report.md
```

Always return exit code 0:

```bash
pyrift scan . --exit-zero
```

---

## Example Finding

A PyRift finding contains more than a rule name.

Conceptually, a result looks like:

```text
CPYxxx
├── location: path/to/file.py:42
├── severity: warning
├── runtime: cpython
├── confidence: high
├── evidence: documentation
├── intent basis: documented
└── suggestion: update or verify the affected usage
```

The exact fields depend on the rule and output format.

The important distinction is that **confidence is evidence-backed**, not an assertion that PyRift knows the developer's intent.

---

## How Intent Is Determined

PyRift does not independently infer:

> "The author intentionally wrote code that relies on this behavior."

Instead, a rule can record an **intent basis** describing why the behavior is considered relevant.

Evidence may include:

- official Python documentation
- Python Enhancement Proposals (PEPs)
- deprecation notices
- removal notes
- version-change documentation
- PyPy implementation/compatibility documentation
- runtime probes or verification
- other explicitly recorded evidence associated with the rule

This allows a finding to distinguish between a documented compatibility change and a heuristic performance warning.

For example:

```text
Documented API removal
→ strong evidence that compatibility changed

Runtime-verified difference
→ direct evidence that observed behavior differs

Performance heuristic
→ possible implementation difference, not proof of a regression
```

See [`docs/behavior-evidence.md`](docs/behavior-evidence.md) for the project's evidence model.

---

## CPython and PyPy

PyRift can analyze code for both:

```text
CPython
  ├── version-to-version compatibility
  │
  └── behavior changes

PyPy
  ├── CPython compatibility differences
  └── implementation/performance differences
```

This is particularly useful for libraries and applications that support more than one Python implementation.

For PyPy-specific findings, PyRift is intentionally conservative: an implementation-specific warning is not automatically presented as a correctness bug.

---

## Runtime Verification

Static analysis is useful, but some behavior differences are best confirmed by executing a focused example.

Where runtime verification is available, PyRift can use it as supporting evidence.

The intended workflow is:

```text
Static pattern detected
        │
        ▼
Known/documented difference?
      /   \
    yes    no
     │      │
     ▼      ▼
 report   investigate
             │
             ▼
       runtime verification
             │
             ▼
       strengthen evidence
```

Runtime verification should complement static analysis rather than replace it.

---

## Output Formats

PyRift currently supports:

| Format | Purpose |
|---|---|
| `text` | Human-readable terminal output |
| `json` | Machine-readable results |
| `markdown` | Reports and review |
| `sarif` | Code-scanning/tool integration |

Example:

```bash
pyrift scan . --format json
```

For SARIF output, PyRift emits stable repository-relative artifact paths so results remain portable between machines and CI environments.

---

## CLI

Show all commands:

```bash
pyrift --help
```

Scan options:

```bash
pyrift scan --help
```

Useful options include:

```text
--format {text,json,markdown,sarif}
--output OUTPUT
--exit-zero
--python-min PYTHON_MIN
--python-max PYTHON_MAX
--platform {windows,linux,macos,posix}
--no-project-config
--no-baseline
--changed-only
--new
--base BASE
```

### Target Python versions

You can constrain the CPython compatibility range:

```bash
pyrift scan . --python-min 3.10 --python-max 3.13
```

This can be useful when a project supports a specific range of Python versions.

### Changed-only scanning

For focused review of a Git change:

```bash
pyrift scan . --changed-only
```

A specific base revision can be supplied:

```bash
pyrift scan . --changed-only --base main
```

### PR/new-finding workflow

PyRift supports baseline-aware review:

```bash
pyrift scan . --new
```

This is intended to help teams focus on newly introduced findings instead of repeatedly reviewing an existing baseline.

---

## Baselines

Baselines allow known findings to be separated from newly introduced findings.

This is useful when adopting PyRift in an existing project where fixing every historical finding immediately is unrealistic.

The goal is:

```text
Existing findings
       │
       ▼
    baseline
       │
       ▼
New code → review only new findings
```

Use the CLI help for the current baseline workflow:

```bash
pyrift baseline --help
```

---

## Rule Catalog

The complete reviewed rule catalog is maintained separately so the README can remain an entry point rather than becoming a large rule reference.

See:

- [`docs/rules.md`](docs/rules.md)
- [`docs/behavior-evidence.md`](docs/behavior-evidence.md)

Each rule is intended to document:

- what pattern it detects
- affected runtime/version
- severity
- evidence
- confidence
- rationale
- suggested remediation
- relevant documentation

---

## Project Structure

```text
PyRift/
├── pyrift/
│   ├── rules/
│   │   ├── cpython/
│   │   └── pypy/
│   ├── scanner.py
│   ├── reporter.py
│   ├── finding.py
│   ├── rule_metadata.py
│   └── cli.py
│
├── tests/
│   ├── cpython/
│   ├── pypy/
│   └── ...
│
├── benchmark/
│   ├── expected.json
│   └── run_benchmark.py
│
├── compatibility-benchmark/
│
├── docs/
│   ├── behavior-evidence.md
│   ├── rules.md
│   └── archive/
│
├── scripts/
│
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
└── pyproject.toml
```

---

## Development

Clone the repository and install it in editable mode:

```bash
python -m pip install -e .
```

Run the complete test suite:

```bash
python -m pytest -q
```

Run CPython rule tests:

```bash
python -m pytest tests/cpython/ -q
```

Run PyPy rule tests:

```bash
python -m pytest tests/pypy/ -q
```

Run linting:

```bash
ruff check .
```

Run the benchmark contract:

```bash
python benchmark/run_benchmark.py
```

Before submitting a change, it is recommended to run:

```bash
ruff check .
python -m pytest -q
python benchmark/run_benchmark.py
git diff --check
```

---

## Adding a Rule

A rule should be based on a specific, reviewable compatibility claim.

A good rule should answer:

1. **What code pattern is being detected?**
2. **Which runtime/version is affected?**
3. **What behavior differs?**
4. **What evidence supports the claim?**
5. **How strong is that evidence?**
6. **Is the finding a correctness issue, compatibility concern, or heuristic?**
7. **What should the user do next?**

Avoid rules that merely encode an unsupported assumption about how Python "should" behave.

For a documented behavior change, link the authoritative source.

For an implementation-specific behavior, make the implementation scope explicit.

For a performance heuristic, avoid presenting it as a correctness failure.

---

## Testing Rules

Every rule should have focused tests covering its intended behavior.

At minimum, consider:

- positive detection
- negative/non-detection cases
- edge cases
- metadata
- affected runtime
- confidence/evidence classification
- interaction with project configuration where relevant

The benchmark suite provides an additional contract layer for reviewed findings.

---

## Documentation

Project documentation is organized as follows:

### Behavior evidence

[`docs/behavior-evidence.md`](docs/behavior-evidence.md)

Explains how PyRift represents evidence, confidence, and intent basis.

### Rule reference

[`docs/rules.md`](docs/rules.md)

Lists the compatibility rules and their documented behavior.

### Project status

- **Version:** 0.8.0
- **Rules:** 120 total (71 CPython + 48 PyPy + 1 cross-runtime)
- **Tests:** 1206 passing
- **Dependencies:** zero
- **Python:** 3.10+

## Contributing

[`CONTRIBUTING.md`](CONTRIBUTING.md)

Explains the contribution workflow and project expectations.

### Security

[`SECURITY.md`](SECURITY.md)

Explains how to report security issues.

### Changelog

[`CHANGELOG.md`](CHANGELOG.md)

Tracks project changes.

---

## Design Principles

### Evidence over assumption

A compatibility finding should be traceable to evidence.

### Conservative reporting

A heuristic should not be presented as a proven bug.

### Runtime-aware analysis

Python behavior is considered in the context of the runtime and version that actually matters.

### Reviewable findings

Findings should contain enough metadata for a developer to understand why they were reported.

### Static analysis first

PyRift should remain useful as a fast static-analysis tool without requiring every scan to execute arbitrary project code.

### Complement runtime testing

Static analysis and runtime testing solve different parts of the compatibility problem. PyRift is intended to help identify where runtime testing deserves attention.

---

## Who Is PyRift For?

PyRift is especially useful for:

- Python library maintainers
- projects supporting multiple Python versions
- projects supporting CPython and PyPy
- developers preparing Python-version upgrades
- CI compatibility checks
- reviewers investigating subtle compatibility changes
- maintainers who want a second layer of static analysis beyond conventional linting

It is not intended to replace:

- unit tests
- integration tests
- type checking
- conventional linters
- runtime compatibility testing

Instead, it complements them.

---

## Current Scope and Limitations

PyRift is an evolving compatibility-analysis project.

Important limitations:

- A finding is not automatically proof that a program is broken.
- Static analysis cannot observe every dynamic Python behavior.
- Some compatibility differences depend on runtime state, platform, extension modules, or implementation details.
- Performance findings are necessarily more heuristic than documented API removals.
- Runtime verification is only available for cases where a safe and meaningful probe can be constructed.
- Supporting a Python version does not mean every behavior difference can be statically detected.

Treat findings as review signals and validate important compatibility claims against the runtimes your project actually supports.

---

## Contributing

Contributions are welcome.

A typical workflow is:

```bash
git clone https://github.com/BHUVANSH855/PyRift.git
cd PyRift

git switch -c fix/my-change

python -m pip install -e .

ruff check .
python -m pytest -q
python benchmark/run_benchmark.py
```

Then open a pull request describing:

- the problem
- the proposed change
- evidence supporting the behavior claim
- tests added or updated
- benchmark impact, if applicable

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for project-specific guidance.

---

## Feedback and Discussion

If you find:

- a false positive
- a missed compatibility difference
- incorrect evidence metadata
- a missing runtime/version case
- an unclear rule explanation
- documentation that could be improved

please open an issue with a minimal reproducible example and, where possible, the relevant Python documentation or runtime evidence.

GitHub Issues and Pull Requests are the preferred place for project discussion and review.

---

## Rule index

| Rule | Title | Severity | Runtime |
|------|-------|----------|---------|
| CPY001 | Dict ordering assumption — comparing dict view to ordered sequence | warning | cpython |
| CPY002 | Exception.add_note() requires Python 3.11+ | warning | cpython |
| CPY003 | X | Y union type syntax requires Python 3.10+ | warning | cpython |
| CPY004 | tomllib requires Python 3.11+ | warning | cpython |
| CPY005 | match/case requires Python 3.10+ | warning | cpython |
| CPY006 | asyncio.timeout() / TaskGroup requires Python 3.11+ | warning | cpython |
| CPY007 | Module removed in Python 3.13 | warning | cpython |
| CPY008 | __slots__ may not prevent __dict__ on Python < 3.10 | warning | cpython |
| CPY009 | ExceptionGroup requires Python 3.11+ | warning | cpython |
| CPY010 | @dataclass(slots=True) requires Python 3.10+ | warning | cpython |
| CPY011 | typing.Self requires Python 3.11+ | warning | cpython |
| CPY012 | typing.LiteralString requires Python 3.11+ | warning | cpython |
| CPY013 | typing.override requires Python 3.12+ | warning | cpython |
| CPY014 | typing.TypeAlias requires Python 3.10+ | warning | cpython |
| CPY015 | typing.Never requires Python 3.11+ | warning | cpython |
| CPY016 | typing.TypeVarTuple requires Python 3.11+ | warning | cpython |
| CPY017 | typing.Unpack requires Python 3.11+ | warning | cpython |
| CPY018 | typing.Required / NotRequired requires Python 3.11+ | warning | cpython |
| CPY019 | distutils removed in Python 3.12+ | warning | cpython |
| CPY020 | datetime.UTC requires Python 3.11+ | warning | cpython |
| CPY021 | asyncio.iscoroutinefunction() deprecated since 3.12 | warning | cpython |
| CPY022 | Bitwise inversion on bool (~True/~False) deprecated in 3.12 | warning | cpython |
| CPY023 | multiprocessing default start method changing in Python 3.14 | warning | cpython |
| CPY024 | typing.TypeGuard requires Python 3.10+ | warning | cpython |
| CPY025 | typing.ParamSpec requires Python 3.10+ | warning | cpython |
| CPY026 | typing.io and typing.re removed in Python 3.13 | warning | cpython |
| CPY027 | locale.resetlocale() removed in Python 3.13 | warning | cpython |
| CPY028 | lib2to3 removed in Python 3.13 | warning | cpython |
| CPY029 | locals() semantics changed in Python 3.13 (PEP 667) | warning | cpython |
| CPY030 | sys.path no longer accepts bytes entries in Python 3.11+ | warning | cpython |
| CPY031 | typing.assert_never requires Python 3.11+ | warning | cpython |
| CPY032 | typing.reveal_type requires Python 3.11+ | warning | cpython |
| CPY033 | pathlib.Path.is_relative_to() requires Python 3.9+ | warning | cpython |
| CPY034 | int.bit_count() requires Python 3.10+ | warning | cpython |
| CPY035 | str.removeprefix/removesuffix requires Python 3.9+ | warning | cpython |
| CPY036 | datetime.utcnow() deprecated since Python 3.12 | warning | cpython |
| CPY037 | datetime.utcfromtimestamp() deprecated since Python 3.12 | warning | cpython |
| CPY038 | asyncio.get_event_loop() raises RuntimeError in Python 3.14+ | warning | cpython |
| CPY039 | zoneinfo module requires Python 3.9+ | warning | cpython |
| CPY040 | graphlib module requires Python 3.9+ | warning | cpython |
| CPY041 | dict | merge operator requires Python 3.9+ | warning | cpython |
| CPY042 | aiter() and anext() builtins require Python 3.10+ | warning | cpython |
| CPY043 | math.lcm() requires Python 3.9+ | warning | cpython |
| CPY044 | math.gcd() with multiple args requires Python 3.9+ | warning | cpython |
| CPY045 | NaN hash behaviour changed in Python 3.10 | warning | cpython |
| CPY046 | open() without encoding= uses platform-dependent encoding before 3.15 | warning | cpython |
| CPY047 | collections.abc.ByteString removed in Python 3.15 | warning | cpython |
| CPY048 | concurrent.interpreters requires Python 3.14+ | warning | cpython |
| CPY049 | compression.zstd requires Python 3.14+ | warning | cpython |
| CPY050 | PurePath.is_reserved() deprecated in 3.13, removed in 3.15 | warning | cpython |
| CPY051 | Unsynchronized module-level mutable state may be unsafe in free-threaded Python | warning | cpython |
| CPY053 | typing.get_overloads() requires Python 3.11+ | warning | cpython |
| CPY054 | int() no longer delegates to __trunc__() in Python 3.14 | warning | cpython |
| CPY055 | NotImplemented in boolean context raises TypeError in Python 3.14 | warning | cpython |
| CPY057 | pickle default protocol changed to 5 in Python 3.14 | warning | cpython |
| CPY062 | string.templatelib requires Python 3.14+ | warning | cpython |
| CPY063 | annotationlib requires Python 3.14+ | warning | cpython |
| CPY064 | Deprecated AST node types removed in Python 3.14 | warning | cpython |
| CPY065 | pkgutil.find_loader()/get_loader() removed in Python 3.14 | warning | cpython |
| CPY066 | asyncio child watcher classes removed in Python 3.14 | warning | cpython |
| CPY067 | typing.NamedTuple keyword syntax deprecated in 3.13, removed in 3.15 | warning | cpython |
| CPY068 | typing.no_type_check_decorator deprecated in 3.13, removed in 3.15 | warning | cpython |
| CPY069 | asyncio.iscoroutinefunction() deprecated in Python 3.14 | warning | cpython |
| CPY070 | asyncio event loop policy deprecated in Python 3.14 | warning | cpython |
| CPY071 | pty.master_open()/slave_open() removed in Python 3.14 | warning | cpython |
| CPY072 | importlib.abc resource classes removed in Python 3.14 | warning | cpython |
| CPY073 | sqlite3.version/version_info removed in Python 3.14 | warning | cpython |
| CPY074 | code.__lnotab__ deprecated since Python 3.10 (PEP 626) | warning | cpython |
| CPY075 | http.server.CGIHTTPRequestHandler deprecated in 3.13, removed in 3.15 | warning | cpython |
| CPY076 | ssl.wrap_socket() removed in Python 3.12 | warning | cpython |
| CPY077 | typing.TypedDict functional syntax deprecated in 3.13, removed in 3.15 | warning | cpython |
| PPY001 | Relying on __del__ for resource cleanup breaks on PyPy | warning | pypy |
| PPY002 | ctypes usage may silently fail on PyPy | warning | pypy |
| PPY003 | sys.getrefcount() is meaningless on PyPy | warning | pypy |
| PPY004 | weakref.proxy() lifetime differs on PyPy due to GC model | warning | pypy |
| PPY005 | File write without explicit lifecycle management on PyPy | warning | pypy |
| PPY006 | Monkey-patching built-in types behaves differently on PyPy | warning | pypy |
| PPY007 | sys.intern() identity guarantees differ on PyPy | warning | pypy |
| PPY008 | threading.local() cleanup timing differs on PyPy | warning | pypy |
| PPY009 | id() stability depends on PyPy GC configuration | warning | pypy |
| PPY010 | gc.collect() behaviour differs on PyPy | warning | pypy |
| PPY011 | array.array('u') type code removed in Python 3.13 | warning | both |
| PPY012 | Overriding built-in methods may behave differently on PyPy | warning | pypy |
| PPY013 | sys.getsizeof() raises TypeError on PyPy | warning | pypy |
| PPY014 | String concatenation in loop is O(n²) on PyPy | warning | pypy |
| PPY015 | Generator cleanup timing differs on PyPy | warning | pypy |
| PPY016 | Instance __dict__ order-sensitive access may differ on PyPy | warning | pypy |
| PPY017 | Adding __del__ to existing class not called on PyPy | warning | pypy |
| PPY018 | sys.setrecursionlimit() behaviour differs on PyPy | warning | pypy |
| PPY019 | float('nan') identity differs between CPython and PyPy | warning | pypy |
| PPY021 | Socket not closed promptly on PyPy — GC timing | warning | pypy |
| PPY022 | PYTHONHASHSEED=0 has no effect on PyPy hash randomisation | warning | pypy |
| PPY023 | inspect.ismethod() returns different results on PyPy | warning | pypy |
| PPY024 | timeit reports average not minimum on PyPy | warning | pypy |
| PPY025 | Set iteration order differs between CPython and PyPy | warning | pypy |
| PPY026 | __builtins__ is always a module on PyPy, never a dict | warning | pypy |
| PPY027 | Deleting module/class attributes may be slower on PyPy | warning | pypy |
| PPY028 | readline.parse_and_bind() silently ignored on PyPy | warning | pypy |
| PPY029 | Assigning to __builtins__ has no effect on PyPy | warning | pypy |
| PPY030 | sys.flags values may differ between CPython and PyPy | warning | pypy |
| PPY031 | Integer 'is' identity semantics differ on PyPy | warning | pypy |
| PPY032 | Mutating dict keys raises RuntimeError on PyPy | warning | pypy |
| PPY033 | Exceptions in __del__ appear at unpredictable times on PyPy | warning | pypy |
| PPY034 | hash() values may differ between CPython and PyPy | warning | pypy |
| PPY035 | C extension packages may not work correctly on PyPy | warning | pypy |
| PPY036 | open() line buffering behaves differently on PyPy | warning | pypy |
| PPY037 | os.urandom() source may differ on PyPy | warning | pypy |
| PPY038 | decimal module uses different backend on PyPy | warning | pypy |
| PPY039 | os.fork() may not work correctly on all PyPy platforms | warning | pypy |
| PPY040 | subprocess.PIPE buffering may cause deadlocks on PyPy | warning | pypy |
| PPY041 | dict | operator requires PyPy 7.3.7+ (Python 3.9 compat) | warning | pypy |
| PPY042 | print(flush=True) may not flush immediately on PyPy | warning | pypy |
| PPY044 | Exception variable cleanup timing differs on PyPy | warning | pypy |
| PPY045 | sys.settrace() disables JIT and is unreliable on PyPy | warning | pypy |
| PPY047 | ctypes.util.find_library() unreliable on PyPy | warning | pypy |
| PPY048 | sys.getsizeof() returns different values on PyPy | warning | pypy |
| PPY049 | GC behavior differs between PyPy and CPython | warning | pypy |
| PPY051 | code.__lnotab__ deprecated on PyPy too | warning | pypy |
| PPY052 | importlib.abc resource classes may differ on PyPy | warning | pypy |
| PPY053 | functools.lru_cache thread safety differs on PyPy | warning | pypy |

## Roadmap

Areas of ongoing development include:

- expanding the CPython compatibility rule catalog
- expanding PyPy compatibility coverage
- improving evidence and confidence metadata
- improving runtime verification
- improving baseline and PR workflows
- improving reporting and CI integration
- making findings easier to investigate interactively
- improving documentation and onboarding

The project is deliberately growing from concrete, evidence-backed compatibility cases rather than attempting to model every possible Python semantic difference at once.

---

## Inspiration and Related Tools

PyRift occupies a space between traditional static analysis and runtime compatibility testing.

Related tools and ideas include:

- [mypy](https://mypy-lang.org/) — static type checking
- [Ruff](https://docs.astral.sh/ruff/) — fast Python linting and formatting
- [Flake8](https://flake8.pycqa.org/) — Python linting
- [Snoop](https://github.com/alexmojaki/snoop) — runtime debugging/tracing
- [SonarQube](https://www.sonarsource.com/products/sonarqube/) — broader static code analysis

PyRift's focus is narrower: **finding Python compatibility and behavior differences that deserve developer attention.**

---

## Acknowledgements

PyRift builds on the work of the Python and PyPy communities and relies heavily on their documentation, specifications, compatibility notes, and implementation knowledge.

The project benefits from feedback from Python developers and maintainers who review the project's approach to compatibility analysis.

---

## License

PyRift is released under the MIT License.

See [`LICENSE`](LICENSE) for the complete license text.

---

## Project Status

PyRift is actively developed.

If the project is useful to you, feedback, issues, documentation improvements, rule proposals, and pull requests are welcome.
