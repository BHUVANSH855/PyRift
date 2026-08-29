---
name: Feature request / new rule
about: Propose a new compatibility rule or feature
title: ""
labels: enhancement
assignees: ""
---

## Feature / rule request

### What is the behaviour difference?

Describe the runtime compatibility difference you have observed between
CPython versions, or between CPython and PyPy. If this is a new rule,
state the pattern it should detect.

### Affected versions / runtimes

- CPython versions affected: _(e.g. 3.12+)_
- PyPy versions affected: _(e.g. all)_
- Evidence basis: _official docs / runtime probe / observed in practice_

### Minimal reproduction

```python
# The pattern that triggers the compatibility difference
```

### Expected detection

What should PyRift report (severity, message, affected version range)?

### Additional context

- Proposed rule ID if you have one (see CONTRIBUTING.md for the inventory).
- Links to official Python or PyPy documentation.
- Any related issue.