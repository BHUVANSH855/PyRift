---
name: Bug report
about: Report a defect in PyRift
title: ""
labels: bug
assignees: ""
---

## Bug report

Thank you for reporting. Please use the checklist below so the issue
can be diagnosed quickly.

### Environment

- PyRift version: _(e.g. 0.8.0, run `pyrift --version`)_
- Python version: _(e.g. 3.12.4, run `python --version`)_
- Operating system: _(e.g. Windows 11, Ubuntu 24.04, macOS 14)_
- Scan mode: _full scan_ / _changed-only_

### What happened

Describe the problem, including the exact command you ran:

```text
pyrift scan . --format text
```

### Minimal reproduction

Provide the smallest possible Python example that reproduces the issue:

```python
import asyncio

loop = asyncio.get_event_loop()
```

### Expected vs. actual output

- **Expected:** what PyRift should report.
- **Actual:** paste the output you saw (or a traceback if PyRift crashed).

### Additional context

- Relevant traceback (if any).
- Whether the issue occurs on a specific rule or version range.

> For **rule** issues, also include the affected Python/runtime versions
> you believe are involved.