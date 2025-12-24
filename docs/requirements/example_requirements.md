# Example Requirements (Template)

This file is a **template** for project-specific UI testing requirements.
Copy it and adapt it to your product. Keep it short, explicit, and testable.

## Core Principles

- **Backend is the source of truth** for validation rules (required/maxLength/pattern/password policy).
- **Frontend assertions must be observable** (UI state, inline errors, aria-invalid, disabled submit).
- **No guessing thresholds**: if rules cannot be proven (snapshot/code), mark as `TBD` and explain why.

## Test Priorities

- **P0**: Page loads + happy path works (write operations must be rollbackable).
- **P1**: Validation matrix (boundary + format + business rules) + key error handling.
- **Security (P1 + security)**: auth/unauth access control, XSS/SQLi payloads do not execute, no 5xx.

