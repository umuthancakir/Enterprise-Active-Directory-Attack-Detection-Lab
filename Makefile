SHELL := /bin/bash
.DEFAULT_GOAL := help

ENV_FILE := .env
LOCAL_DIR := infra/local

# ---- environment ----------------------------------------------------------

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: check-env
check-env:
	@test -f $(ENV_FILE) || (echo "Missing .env — copy .env.example to .env and fill it in." && exit 1)

.PHONY: check-tools
check-tools: ## Verify required local tooling is installed
	@command -v packer >/dev/null 2>&1 || (echo "packer not found — see README.md Prerequisites" && exit 1)
	@command -v qemu-system-x86_64 >/dev/null 2>&1 || (echo "qemu not found — see README.md Prerequisites" && exit 1)
	@command -v ansible >/dev/null 2>&1 || (echo "ansible not found — see README.md Prerequisites" && exit 1)
	@echo "All required tools found."

# ---- lab lifecycle (DEPLOY_TARGET=local, UTM/QEMU — see docs/adr/0004) ----
#
# `make up` does NOT fully automate VM boot: UTM has no CLI to start a VM
# from a script in a way this project has been able to verify (see
# infra/local/README.md), so after this target you still open UTM and start
# the 4 generated VMs by hand, then run `make sync-scope`. See
# infra/local/README.md "Build → generate → boot → sync" for the full,
# honest step-by-step.

.PHONY: up
up: check-env check-tools ## Build images + generate UTM bundles (see infra/local/README.md for the manual boot step this can't automate)
	$(LOCAL_DIR)/build.sh dc01
	$(LOCAL_DIR)/build.sh mem01
	$(LOCAL_DIR)/build-linux.sh attacker01
	$(LOCAL_DIR)/build-linux.sh siem01
	python3 $(LOCAL_DIR)/generate_bundles.py
	@echo ""
	@echo "Bundles generated. Open UTM, start dc01/mem01/attacker01/siem01,"
	@echo "then run: make sync-scope"

.PHONY: down
down: ## Tear down the lab: delete generated bundles + built images
	@echo "Delete each .utm bundle from UTM's VM library (see infra/local/state.json for paths),"
	@echo "then: rm -rf $(LOCAL_DIR)/build $(LOCAL_DIR)/state.json"
	## STATUS: not scripted further than this — deleting a running VM's
	## bundle out from under UTM needs the VM stopped first, which this
	## Makefile can't confirm without the UTM CLI verification called out in
	## infra/local/README.md. See ROADMAP.md.

.PHONY: sync-scope
sync-scope: ## Refresh inventory/lab-scope.yaml from infra/local/state.json + discovered-ips.yaml
	python3 scripts/sync_scope.py

# ---- attack / detections ----------------------------------------------------
#
# `make attack` defaults to --dry-run: it resolves targets through the
# scope guard, prints the exact command each technique would run, and
# emits Finding records from attack/fixtures/ — no tool is actually
# invoked. This is real and works right now, against the real (currently
# unprovisioned) inventory/lab-scope.yaml, which is exactly why it safely
# refuses until `make sync-scope` has run against an actual provisioned
# lab. Pass MODE=live once a lab exists to actually run tooling — see
# attack/runner.py's module docstring; that path is unexercised by any
# test here.

.PHONY: attack
attack: check-env ## Run an attack chain (dry-run by default) against in-scope hosts only. Usage: make attack SCENARIO=<name> [MODE=live]
	@test -n "$(SCENARIO)" || (echo "Usage: make attack SCENARIO=<name> [MODE=live]" && exit 1)
	python3 -m attack.runner --scenario $(SCENARIO) $(if $(filter live,$(MODE)),--live,--dry-run)

.PHONY: detections-test
detections-test: ## Validate Sigma rules and run detection tests against captured telemetry
	python3 -m detections.test_runner  ## STATUS: STUB — see ROADMAP.md Phase 4

# ---- platform -----------------------------------------------------------

.PHONY: platform
platform: check-env ## Serve the platform (backend + frontend) locally via docker compose
	docker compose -f platform/docker-compose.yml up --build  ## STATUS: STUB — see ROADMAP.md Phase 5

# ---- quality -----------------------------------------------------------
#
# Every tool below is pip-installable at user level (`pip install --user
# ...`, no sudo) except packer itself, which needs Homebrew — see
# ROADMAP.md "Known blockers". `lint`/`test` degrade gracefully (skip with
# a clear message) rather than failing outright when a given tool truly
# isn't installed, but CI (.github/workflows/ci.yml) always has every tool
# and does not get that grace — CI failing is the real signal.

.PHONY: lint
lint: ## Run all linters: ruff, mypy, ansible-lint, packer fmt/validate (where installed)
	@echo "--- ruff ---"; ruff check .
	@echo "--- mypy ---"; mypy
	@echo "--- ansible-lint (config/) ---"; ansible-lint config/
	@if command -v packer >/dev/null 2>&1; then \
		echo "--- packer fmt -check ---"; packer fmt -check -recursive $(LOCAL_DIR)/packer; \
	else \
		echo "--- packer fmt -check: SKIPPED (packer not installed — see README.md Prerequisites) ---"; \
	fi

.PHONY: test
test: ## Run the pytest suite (attack/lib scope guard, sync_scope, dynamic inventory)
	pytest
