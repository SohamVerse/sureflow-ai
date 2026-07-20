# Security Policy

<!-- Copyright © 2026 Team Hogwart. All Rights Reserved. -->

<div align="center">

![Security Policy](https://img.shields.io/badge/Security-Policy-crimson?style=for-the-badge&logo=shieldsdotio&logoColor=white)
![Proprietary](https://img.shields.io/badge/License-Proprietary-darkred?style=for-the-badge)
![Team Hogwart](https://img.shields.io/badge/Team-Hogwart-6C3483?style=for-the-badge)

</div>

---

## Overview

Team Hogwart takes the security of **SureFlow AI** and all related systems seriously. We are committed to responsible vulnerability disclosure and will work with security researchers in good faith to resolve confirmed issues as quickly as possible.

> **⚠️ This repository contains proprietary and confidential software. All security communications must be treated as strictly confidential and must not be publicly disclosed.**

---

## Supported Versions

The following versions are actively maintained and eligible to receive security patches:

| Version | Status          | Security Fixes |
|---------|-----------------|---------------|
| 2.x     | ✅ Active        | Supported      |
| 1.x     | ⚠️ Maintenance  | Critical only  |
| < 1.0   | ❌ End of Life   | Not supported  |

We strongly recommend always running the latest version.

---

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub Issues, pull requests, or discussions.**

If you believe you have discovered a security vulnerability in SureFlow AI, we ask that you follow our responsible disclosure process:

### 📧 Step 1 — Contact Us Privately

Send your vulnerability report to:

```
Security Contact:  [security@placeholder.teamhogwart.com]
PGP Key:          [Available upon request]
```

### 📋 Step 2 — Include the Following Information

To help us triage and resolve the issue efficiently, please include:

- **Description** of the vulnerability and its potential impact
- **Steps to reproduce** the issue, with as much detail as possible
- **Affected component(s)** — e.g., backend API, authentication, AI workflow, database
- **Proof-of-concept** or exploit code (if applicable and safe to share)
- **Suggested fix** (optional, but appreciated)
- **Your contact information** (for follow-up)

### 🔒 Step 3 — Confidential Handling

- Do not share or publish the vulnerability details until we have issued a patch and publicly acknowledged the report (if applicable)
- Do not access, modify, or delete any data you are not authorized to access
- Do not perform actions that could cause disruption, data loss, or service unavailability

---

## Response Timeline

We are committed to the following response SLA:

| Milestone                     | Target Timeframe |
|-------------------------------|-----------------|
| Acknowledgement of receipt    | Within 48 hours  |
| Initial assessment            | Within 5 business days |
| Status update to reporter     | Within 10 business days |
| Patch or mitigation deployed  | Varies by severity |

Response times may vary depending on severity, complexity, and availability of the team.

---

## Severity Classification

We use the following severity tiers to prioritize security issues:

| Severity     | Description                                                         |
|--------------|---------------------------------------------------------------------|
| 🔴 Critical  | Remote code execution, full data breach, authentication bypass     |
| 🟠 High      | Privilege escalation, significant data exposure, injection attacks  |
| 🟡 Medium    | Limited data exposure, CSRF, insecure configuration                |
| 🟢 Low       | Informational, minor misconfigurations, hardening recommendations  |

---

## Scope

The following assets are **in scope** for security research:

- SureFlow AI backend API (`/api/v1/*`)
- Authentication and authorization mechanisms (JWT, RBAC)
- Document ingestion pipeline
- AI agent endpoints and workflows
- Database access and query patterns

The following are **out of scope**:

- Third-party services (Google Gemini, Neo4j Aura, Vercel, Render)
- Social engineering attacks targeting Team Hogwart members
- Physical security attacks
- Denial-of-service (DoS) attacks

---

## Responsible Disclosure & Recognition

Team Hogwart follows a **coordinated disclosure** model. Researchers who responsibly disclose vulnerabilities will:

- Receive written acknowledgement of their contribution
- Be credited in our security acknowledgements (if they wish)
- Not face legal action for good-faith security research conducted within this policy

We do not currently offer a monetary bug bounty program.

---

## Legal

This security policy is provided for good-faith security researchers. Any security testing that is conducted outside the boundaries described here, or that causes disruption to our systems or data, may violate applicable computer crime laws and the terms of our proprietary license.

Team Hogwart reserves all legal rights with respect to unauthorized access or testing.

---

<div align="center">

**SureFlow AI** — Developed during ET AI Hackathon 2.0

© 2026 Team Hogwart · All Rights Reserved · Proprietary & Confidential

</div>
