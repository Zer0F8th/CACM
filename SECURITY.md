# Security Policy

This document describes how to report security vulnerabilities for **CACM (CIP Asset Configuration Manager)** and what to expect from the maintainers.

> **Do not** create public GitHub issues for suspected security vulnerabilities.

---

## Reporting a Vulnerability

Please report suspected vulnerabilities by emailing:

**Zer0F8th@gmail.com**

Include as much of the following as possible:

- A clear description of the issue and potential impact
- Steps to reproduce (proof-of-concept code is helpful, but keep it minimal)
- Affected component(s) and version(s) (CACM version, commit hash, container tag, etc.)
- Environment details (OS, deployment method, config, integration points)
- Any relevant logs, screenshots, or packet captures (redact secrets)
- Whether you have attempted exploitation beyond basic validation (please avoid destructive testing)

If the issue involves **OT/ICS environments**, include:
- Whether the finding impacts availability/safety (e.g., could disrupt a control center workflow)
- Any assumptions about network segmentation, jump hosts, and privileged access

### Sensitive Data
Please **do not** send secrets (API keys, passwords, bearer tokens, private keys) in plain text. If you must share sensitive info for reproduction, ask for a secure channel first.

---

## Supported Versions

CACM is under active development. Security fixes will generally be provided for:

- **The latest release**
- **The `main` branch** (for users building from source)

If you are running an older commit or fork, we may ask you to reproduce the issue on a supported version before we proceed.

---

## Disclosure Policy

We follow a coordinated disclosure approach:

1. **Acknowledge receipt**: We will confirm we received your report.
2. **Triage**: We’ll assess severity, scope, and affected components.
3. **Mitigation & fix**: We’ll work on a fix and/or recommended mitigations.
4. **Release & advisory**: We may publish an advisory and credit reporters (with permission).

### Typical Response Targets (Best Effort)
Timelines depend on severity and maintainer availability, but our targets are:

- **Acknowledgement**: within **3 business days**
- **Initial triage**: within **7 business days**
- **Fix or mitigation guidance**:
  - **Critical**: ~**7–14 days**
  - **High**: ~**14–30 days**
  - **Medium/Low**: best effort, often bundled with regular releases

If you have a deadline (e.g., academic submission, vendor disclosure window), include it in your report.

---

## Scope

### In Scope
Examples include (not exhaustive):

- Remote code execution (RCE), authentication bypass, privilege escalation
- Exposure of secrets (tokens, credentials), insecure default configurations
- Authorization flaws (IDOR), SSRF, path traversal, injection vulnerabilities
- Supply chain risks in dependencies or build/release artifacts
- Insecure network services, unsafe deserialization, insecure file handling
- Vulnerabilities affecting integrations (e.g., collectors/agents, APIs, message queues)

### Out of Scope
- Vulnerabilities only affecting unsupported versions
- Issues requiring physical access without realistic threat model
- Social engineering, phishing of maintainers/users
- DoS findings that rely on overwhelming traffic without a practical exploit path
- Low-impact best-practice suggestions without a security boundary violation
  (still welcome as regular issues/PRs)

---

## Security Considerations for CACM Deployments

CACM is designed for environments that may include **regulated** or **critical infrastructure** networks. We recommend:

- Run CACM services with **least privilege** and **non-root** containers where possible
- Keep dependencies updated and use dependency scanning (e.g., Dependabot)
- Protect API endpoints behind strong auth (SSO/OIDC where feasible)
- Store secrets in a secure secret manager (not in `.env` committed to source)
- Enable TLS for all network paths and validate certificates
- Segment networks (management plane separated from monitored assets)
- Log security-relevant events (auth, config changes, baseline updates, admin actions)
- Treat “baseline configuration” and inventory data as sensitive

---

## Public Communication

If a vulnerability is confirmed, we may:

- Publish a GitHub Security Advisory (preferred when available)
- Document mitigations/workarounds
- Credit the reporter (optional)

We will avoid publishing exploit details before a fix is available.

---

## Security Testing

If you want to test CACM:

- Use a **non-production** environment whenever possible
- Avoid testing that could disrupt OT/ICS availability or safety
- Coordinate with maintainers if your testing may affect shared infrastructure

---

## Contact

Security reports: **Zer0F8th@gmail.com**

Project repository: CACM (CIP Asset Configuration Manager)

---

_Last updated: 2026-02-11_
