# J.A.R.V.I.S. Security & Hardening Model

## Core Security Principles

The J.A.R.V.I.S. ecosystem executes automated operations on Windows with strict defensive controls:

### 1. Loopback Binding & Public Internet Isolation
- The desktop automation service binds exclusively to local loopback `127.0.0.1`.
- It is never exposed to public internet interfaces or remote networks.

### 2. Local Pairing Token Authentication
- Communications between the AI Backend and Desktop Agent require a shared secret Bearer token.
- Unauthenticated requests receive HTTP `401 Unauthorized`.

### 3. Application Execution Allowlist
- Arbitrary shell commands are completely disabled.
- The desktop agent utilizes `subprocess.Popen([exe], shell=False)` only against pre-approved application keys defined in `desktop_agent/config.json`.
- Any unapproved binary name is immediately rejected.

### 4. Interactive Human-in-the-Loop Interlocks
- Potentially sensitive actions (e.g. launching Command Prompt, terminating processes, or executing developer workflows) require explicit user authorization.
- The agent generates a temporary approval record with a 5-minute time-to-live (TTL). The user must confirm via the UI or voice verification before execution proceeds.

### 5. Sandboxed File Operations & Traversal Prevention
- File searching, reading, and writing are restricted to authorized root paths (e.g., project workspace, user Documents, Desktop).
- Path traversal sequences (`../`, canonical symlinks, or parent deviations) are caught via `Path.resolve()` checks and blocked.

### 6. Zero Secret Leakage
- API keys stored in configuration are masked (`sk-...xxxx`) in client responses.
- Raw keys and credentials are never emitted in client JavaScript bundles or application activity streams.
