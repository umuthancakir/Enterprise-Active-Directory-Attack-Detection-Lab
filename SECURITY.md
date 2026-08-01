# Security Policy

## What this project is

EADADL is a purple-team laboratory and orchestration platform. It intentionally
provisions a **vulnerable** Active Directory environment and runs **real,
publicly documented offensive tooling** against it, on purpose, for detection
engineering and training. Standard "report a CVE" security policies do not
apply to the lab environment itself — it is vulnerable by design.

This document covers (1) the safety invariants that keep that intentional
vulnerability contained, and (2) how to report a problem with the platform
code (backend/frontend/CI) that is *not* an intended lab weakness.

## Safety invariants (non-negotiable)

These are enforced in code and config, not just documentation:

1. **Network isolation.** The lab network is host-only / internal with no
   route to the internet or any system outside the lab. It is provisioned
   fresh from code and is disposable.
2. **Scope guard.** All attack automation reads
   [`inventory/lab-scope.yaml`](inventory/lab-scope.yaml) at runtime. Any
   target not listed there is refused before any offensive action is taken.
   There is no override flag and no "arbitrary target" mode. See
   [`docs/adr/0002-scope-guard.md`](docs/adr/0002-scope-guard.md).
3. **No novel exploit code.** The `attack/` engine orchestrates established,
   publicly documented open-source tooling (NetExec, Impacket, BloodHound/
   SharpHound, PowerView, Atomic Red Team, Caldera). It does not implement
   original exploits, malware, or evasion/obfuscation payloads. Every
   technique maps to a published MITRE ATT&CK ID with a reference link.
4. **Ephemeral.** `make down` fully tears the environment down. Nothing the
   lab produces persists outside this repository except intended artifacts
   (reports, detections, logs) that are explicitly exported.
5. **No real secrets or PII.** All lab identities, credentials, and data are
   synthetic. Real credentials are never committed; `.env` is gitignored and
   `.env.example` documents the required variables with placeholder values.

## Reporting a platform vulnerability

If you find a vulnerability in the platform code itself (e.g. the FastAPI
backend, auth/RBAC, the React frontend, or CI) — as opposed to an intentional
lab weakness documented in [`docs/vulnerabilities.md`](docs/vulnerabilities.md)
— please open a private security advisory on this repository rather than a
public issue. Include reproduction steps and affected component/version.

## Authorized use only

This project is for use in isolated lab environments that you own or are
explicitly authorized to test. See the disclaimer in [README.md](README.md)
for the full authorized-use notice. Do not point any tooling in this
repository at systems you do not own or have written authorization to test.
