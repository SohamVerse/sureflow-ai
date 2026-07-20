# Contributing Guidelines

<!-- Copyright © 2026 Team Hogwart. All Rights Reserved. -->

<div align="center">

![Proprietary](https://img.shields.io/badge/License-Proprietary-darkred?style=for-the-badge)
![Internal Only](https://img.shields.io/badge/Contributors-Internal%20Only-6C3483?style=for-the-badge)
![Team Hogwart](https://img.shields.io/badge/Team-Hogwart-4A235A?style=for-the-badge)

</div>

---

> **⚠️ IMPORTANT — External Contributions Not Accepted**
>
> SureFlow AI is **proprietary, confidential software** owned exclusively by Team Hogwart. This repository is **not open source** and does **not** accept unsolicited external contributions of any kind — including pull requests, patches, bug fixes, or feature suggestions — unless explicitly authorized in writing by an authorized representative of Team Hogwart.
>
> Unauthorized submissions do not grant any rights or claims over this software. See the [`LICENSE`](./LICENSE) file for complete terms.

---

## For Internal Contributors

This document defines the standards, workflows, and conventions that all authorized Team Hogwart members must follow when contributing to this codebase. Adherence to these standards ensures code quality, security, and maintainability across the project.

---

## 1. Coding Standards

### General Principles

- Write **clean, readable, and self-documenting code**. Clarity is preferred over cleverness.
- Follow the **principle of least privilege** — request only the permissions and access a component genuinely needs.
- Keep functions and modules **small and focused** — each should do one thing well.
- All new code must include appropriate **copyright headers** (see template below).
- Do not commit **secrets, API keys, credentials, or PII** to the repository under any circumstances.

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use **type hints** for all function signatures
- Format code with `black` and lint with `ruff`
- Maximum line length: **100 characters**
- Use `pydantic` models for all request/response schemas
- Async-first: prefer `async def` for all I/O-bound operations
- Document all public functions and classes with docstrings

```bash
# Format and lint before committing
black backend/
ruff check backend/ --fix
mypy backend/ --ignore-missing-imports
```

### TypeScript / JavaScript (Frontend)

- Strict TypeScript: `"strict": true` in `tsconfig.json`
- Use **functional components** with React hooks — no class components
- Use `const` and `let`; never `var`
- Format with `prettier` and lint with `eslint`
- Name components in `PascalCase`, utilities in `camelCase`, constants in `UPPER_SNAKE_CASE`

```bash
# Format and typecheck before committing
cd frontend
npx prettier --write src/
npx tsc --noEmit
npx eslint src/ --fix
```

### SQL

- Use descriptive, lowercase table and column names with `_` separators
- Always use parameterized queries — never string-interpolate user input into SQL
- Include migration files for all schema changes (Alembic)
- Comment complex queries explaining intent

---

## 2. Branch Naming Conventions

All branches must follow this naming scheme:

```
<type>/<short-description>
```

| Type         | Use for                                      | Example                        |
|--------------|----------------------------------------------|--------------------------------|
| `feature/`   | New features or functionality                | `feature/compliance-agent`     |
| `fix/`       | Bug fixes                                    | `fix/neo4j-connection-timeout` |
| `hotfix/`    | Critical production fixes                    | `hotfix/jwt-auth-bypass`       |
| `refactor/`  | Code restructuring without behavior change   | `refactor/model-broker-cleanup`|
| `docs/`      | Documentation updates only                  | `docs/deployment-guide`        |
| `chore/`     | Build scripts, config, tooling changes       | `chore/update-dependencies`    |
| `test/`      | Test additions or improvements               | `test/agent-unit-tests`        |

**Rules:**
- Use lowercase only; separate words with hyphens
- Keep descriptions concise (3–6 words)
- Never commit directly to `main` or `develop`

---

## 3. Commit Message Conventions

Follow the **Conventional Commits** specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

### Types

| Type       | When to use                                     |
|------------|-------------------------------------------------|
| `feat`     | A new feature                                   |
| `fix`      | A bug fix                                       |
| `docs`     | Documentation changes only                      |
| `style`    | Formatting, whitespace (no logic changes)       |
| `refactor` | Code restructuring (no feature or fix changes)  |
| `perf`     | Performance improvements                        |
| `test`     | Adding or modifying tests                       |
| `chore`    | Build process, dependencies, tooling            |
| `security` | Security hardening or vulnerability patches     |

### Examples

```
feat(agents): add MTBF prediction to maintenance agent

Implements cross-asset failure probability scoring using historical
incident data from the knowledge graph. Adds BrainOutput fields for
confidence intervals and recommended maintenance windows.

Closes #42
```

```
fix(auth): resolve JWT expiry edge case on token refresh

Token refresh was failing when the refresh token arrived exactly at
expiry boundary. Fixed by using server-side timestamp comparison.
```

**Rules:**
- Subject line: max **72 characters**, imperative mood ("add", not "added")
- No period at end of subject line
- Reference issue numbers in footer where applicable
- Body: explain *what* and *why*, not *how*

---

## 4. Pull Request Workflow

### Before Opening a PR

- [ ] Branch is up to date with `develop` (rebase, don't merge)
- [ ] All linting and formatting checks pass
- [ ] TypeScript type checks pass (`npx tsc --noEmit`)
- [ ] No secrets or sensitive data in the diff
- [ ] Copyright headers present on all new files
- [ ] Relevant documentation updated (if applicable)

### PR Requirements

- **Title**: Follow commit convention format — `feat(scope): description`
- **Description**: Fill in the PR template completely
  - What does this PR do?
  - How was it tested?
  - Are there any breaking changes?
  - Related issue(s) / ticket(s)
- **Size**: Keep PRs small and focused — aim for < 400 lines of diff. Large PRs must be discussed before opening.

### PR Labels

Use appropriate labels:
`feature` · `bug` · `security` · `documentation` · `breaking-change` · `needs-review` · `do-not-merge`

---

## 5. Code Review Requirements

All code merged into `develop` or `main` **must** pass code review. No self-merges are permitted.

### Reviewer Responsibilities

- Review for **correctness, security, performance, and adherence to standards**
- Run the code locally if the change is non-trivial
- Leave constructive, specific, and respectful feedback
- Mark comments as `blocking` or `non-blocking` (suggestion)
- Approve only when all blocking comments are resolved

### Author Responsibilities

- Respond to all review comments
- Mark your own comments as resolved after addressing them
- Do not resolve reviewer comments — let the reviewer do so
- Request re-review after making significant changes

### Merge Criteria

- ✅ At least **1 approval** from a core team member
- ✅ All CI checks pass
- ✅ All blocking review comments resolved
- ✅ No merge conflicts

---

## 6. Copyright Header Requirements

All new source files must include the appropriate copyright header. See the templates below.

### Python

```python
# ============================================================================
# Copyright © 2026 Team Hogwart. All Rights Reserved.
# SureFlow AI — Intelligent Multi-Agent Knowledge Engine for Industrial Operations
#
# Developed during ET AI Hackathon 2.0.
#
# PROPRIETARY AND CONFIDENTIAL. Unauthorized copying, modification,
# distribution, reverse engineering, or commercial use without prior
# written permission from Team Hogwart is strictly prohibited.
# ============================================================================
```

### TypeScript / JavaScript

```typescript
// ============================================================================
// Copyright © 2026 Team Hogwart. All Rights Reserved.
// SureFlow AI — Intelligent Multi-Agent Knowledge Engine for Industrial Operations
//
// Developed during ET AI Hackathon 2.0.
//
// PROPRIETARY AND CONFIDENTIAL. Unauthorized copying, modification,
// distribution, reverse engineering, or commercial use without prior
// written permission from Team Hogwart is strictly prohibited.
// ============================================================================
```

---

## 7. Security Guidelines for Internal Contributors

- **Never** hard-code secrets, API keys, tokens, or passwords in source code
- Use environment variables (`.env`) and reference `.env.example` for templates
- All `.env` files are in `.gitignore` — verify before each commit
- Report any discovered security vulnerabilities via the process in [SECURITY.md](./SECURITY.md)
- All external inputs must be validated and sanitized before processing

---

<div align="center">

**SureFlow AI** — Developed during ET AI Hackathon 2.0

© 2026 Team Hogwart · All Rights Reserved · Proprietary & Confidential

</div>
