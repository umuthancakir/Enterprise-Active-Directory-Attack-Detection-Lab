# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Phase 0 repo scaffold: directory layout, governance docs (README,
  SECURITY, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT), ADR framework,
  `inventory/lab-scope.yaml` scope guard contract, `.env.example`, Makefile
  skeleton, CI skeleton.
- ADR 0001: deploy target set to Azure (`DEPLOY_TARGET=azure`).
- ADR 0002: scope guard contract for attack automation.
- Phase 1 (partial): `infra/azure/` Terraform for the isolated AD lab
  (resource group, vnet, NSGs, Bastion, all 5 VMs), code-only, never
  applied. `docs/vulnerabilities.md` (8 planned misconfigs mapped to
  ATT&CK). `scripts/sync_scope.py`.

### Changed

- ADR 0004: deploy target reverted from Azure to local UTM/QEMU;
  `infra/azure/` removed in favor of `infra/local/` (Packer + UTM bundle
  generator). ADR 0005: local network isolation model (UTM Host Only).
  Footprint trimmed to 4 hosts (`dc01`, `mem01`, `attacker01`, `siem01`) —
  standalone `wks01` workstation deferred, see `docs/vulnerabilities.md`.
