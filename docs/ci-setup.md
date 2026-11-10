# CI Setup

## GitHub Actions

`pyrift` can annotate pull requests with inline diff comments by using the
`--format github` output mode.  The formatter emits GitHub
[workflow commands](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#setting-an-error-message)
(`::error`, `::warning`, `::notice`) that the GitHub Actions runner
converts into inline annotations automatically.

### Minimal workflow

```yaml
name: pyrift

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install pyrift
        run: pip install pyrift

      - name: Run pyrift
        run: pyrift scan --format github .
```

### Filter to documented changes only

Add `--only-documented` to limit annotations to findings backed by an
official CPython PEP, What's New entry, or explicit deprecation notice:

```yaml
      - name: Run pyrift (documented changes only)
        run: pyrift scan --format github --only-documented .
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | No findings (clean run) |
| `1`  | One or more findings produced |
| `2`  | Usage or configuration error |

Set `continue-on-error: true` on the step if you want the workflow to
succeed even when findings are present (annotations will still appear).

## Other CI systems

For CI systems that do not interpret GitHub workflow commands, use
`--format text` (default), `--format json`, or `--format sarif`.
SARIF output can be uploaded to any SARIF-aware platform, including
GitHub Code Scanning:

```yaml
      - name: Run pyrift (SARIF)
        run: pyrift scan --format sarif . > pyrift.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: pyrift.sarif
```
