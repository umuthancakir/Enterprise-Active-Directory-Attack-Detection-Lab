# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). For a
session-by-session narrative (including what was tried, found broken, and
fixed), see [BUILD_LOG.md](BUILD_LOG.md) — this file is the condensed,
release-note-style summary.

## [Unreleased]

### Added

- Phase 0 scaffold: directory layout, governance docs, ADR framework,
  scope-guard contract, `.env.example`, Makefile, CI.
- `attack/`: scope guard (`attack/lib/scope_guard.py`, fail-closed, no
  bypass path), a 6-technique registry, 2 attack chains
  (`credential_harvest`, `domain_dominance`), and a dry-run-first runner
  (`make attack SCENARIO=<name>`) — genuinely runnable and tested without
  a live lab.
- `detections/`: 6 Sigma rules (one per technique), a fixture-based test
  harness that reuses pySigma's real condition parser
  (`detections/matcher.py`), and a committed attack→detection coverage
  matrix (`make detections-test`).
- `telemetry/`: Sysmon config, Windows Security audit-policy/SACL scripts,
  WEF subscription, Winlogbeat + Elasticsearch/Kibana config.
- `config/`: Ansible roles promoting the AD forest, joining the member
  server, and implementing 6 of 8 documented deliberate misconfigurations.
- `platform/`: FastAPI backend (JWT auth, viewer/operator RBAC, scenario
  runner API, run history, coverage API — fully tested) + Next.js
  frontend (dashboard, run detail, coverage heatmap) + Docker Compose.
- `ir/`: 5 NIST SP 800-61 incident-response playbooks, a threat-hunting
  Jupyter notebook, and dry-run-only SOAR-style response automation.
- `docs/architecture.md`: telemetry data-flow, attack-chain, and
  purple-team-loop diagrams.
- ADRs 0001–0006 covering deploy-target selection (and its later
  reversal), the scope-guard contract, network isolation (both the
  original Azure design and its local-UTM replacement), and the telemetry
  architecture.

### Changed

- Deploy target reverted from Azure (ADR 0001) to local UTM/QEMU (ADR
  0004) — `infra/azure/` removed in favor of `infra/local/` (Packer + a
  UTM bundle generator). Lab footprint trimmed from 5 hosts to 4
  (`dc01`, `mem01`, `attacker01`, `siem01`) — see `docs/vulnerabilities.md`
  for what that deferred.

### Known limitations (see ROADMAP.md for the full, itemized breakdown)

- Nothing has been provisioned or run against a real host — this account
  has no admin/sudo rights, which blocks Homebrew and everything that
  needs it (Packer, QEMU, UTM automation, Node.js, Docker). Python and
  Ansible tooling install fine at user level and are genuinely tested;
  the local-lab and frontend/container layers are written but unverified.
