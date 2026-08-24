# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.5.x | ✅ Active |
| 0.4.x | ✅ Active |
| 0.3.x | ⚠️ Security fixes only |
| 0.2.x | ❌ No longer supported |
| 0.1.x | ❌ No longer supported |

## Reporting a vulnerability

If you discover a security vulnerability in pyrift itself, please do
**not** open a public GitHub issue.

Report it privately by emailing: **bhuvanshkataria@email.com**

Please include:
- A description of the vulnerability
- Steps to reproduce it
- The version of pyrift affected
- Any suggested fix if you have one

You will receive a response within 72 hours. If the vulnerability is
confirmed, a fix will be released as soon as possible and you will be
credited in the changelog unless you prefer to remain anonymous.

## Scope

pyrift is a static analysis tool — it reads Python source files and
produces findings. It does not execute user code, make network requests,
or write files outside the specified output path.

## What is in scope

- Vulnerabilities in pyrift's own code
- False negatives that cause pyrift to miss known dangerous patterns
- Denial of service via malformed Python source files
- Path traversal in file scanning

## What is out of scope

- Vulnerabilities in the Python code that pyrift is analysing
- Issues with packages that pyrift is installed alongside
- Feature requests disguised as security issues