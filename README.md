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

### Contributing

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
