# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.8.x | ✅ Active |
| 0.7.x | ⚠️ Security fixes only |
| 0.6.x | ⚠️ Security fixes only |
| 0.5.x and older | ❌ No longer supported |

## Reporting a vulnerability

If you discover a security vulnerability in pyrift itself, please do
**not** open a public GitHub issue.

Report it privately by emailing:

`bhuvanshkataria@email.com`

Please include:

- A description of the vulnerability
- Steps to reproduce it
- The version of pyrift affected
- Any suggested fix if available

You will receive a response within 72 hours.

If the vulnerability is confirmed, a fix will be released as soon as
reasonably possible and you will be credited in the changelog unless
you prefer to remain anonymous.

## Scope

pyrift is a static analysis tool. It reads Python source files and
produces findings. It does not execute the user's analysed program,
make network requests, or intentionally write files outside the
specified output path.

## What is in scope

- Vulnerabilities in pyrift's own code
- False negatives that cause pyrift to miss known dangerous patterns
- Denial of service caused by malformed Python source files
- Path traversal in file scanning
- Unsafe handling of baseline or report files

## What is out of scope

- Vulnerabilities in the Python code being analysed
- Vulnerabilities in packages that pyrift is installed alongside
- General feature requests
- False positives that do not create a security impact