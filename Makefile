SHELL := /bin/bash
.DEFAULT_GOAL := help

ENV_FILE := .env
TF_DIR := infra/azure

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
	@command -v terraform >/dev/null 2>&1 || (echo "terraform not found — see README.md Prerequisites" && exit 1)
	@command -v az >/dev/null 2>&1 || (echo "az CLI not found — see README.md Prerequisites" && exit 1)
	@command -v ansible >/dev/null 2>&1 || (echo "ansible not found — see README.md Prerequisites" && exit 1)
	@echo "All required tools found."

# ---- lab lifecycle ----------------------------------------------------------

.PHONY: up
up: check-env check-tools ## Provision the isolated AD lab (terraform apply)
	cd $(TF_DIR) && terraform init && terraform apply

.PHONY: down
down: check-env check-tools ## Tear down the isolated AD lab (terraform destroy)
	cd $(TF_DIR) && terraform destroy

.PHONY: plan
plan: check-env check-tools ## Show the terraform plan without applying
	cd $(TF_DIR) && terraform init && terraform plan

.PHONY: sync-scope
sync-scope: ## Refresh inventory/lab-scope.yaml from terraform outputs
	python3 scripts/sync_scope.py  ## STATUS: STUB — see ROADMAP.md Phase 1

# ---- attack / detections ----------------------------------------------------

.PHONY: attack
attack: check-env ## Run an attack chain against in-scope hosts only. Usage: make attack SCENARIO=<name>
	@test -n "$(SCENARIO)" || (echo "Usage: make attack SCENARIO=<name>" && exit 1)
	python3 -m attack.runner --scenario $(SCENARIO)  ## STATUS: STUB — see ROADMAP.md Phase 3

.PHONY: detections-test
detections-test: ## Validate Sigma rules and run detection tests against captured telemetry
	python3 -m detections.test_runner  ## STATUS: STUB — see ROADMAP.md Phase 4

# ---- platform -----------------------------------------------------------

.PHONY: platform
platform: check-env ## Serve the platform (backend + frontend) locally via docker compose
	docker compose -f platform/docker-compose.yml up --build  ## STATUS: STUB — see ROADMAP.md Phase 5

# ---- quality -----------------------------------------------------------

.PHONY: lint
lint: ## Run all linters (terraform fmt, ansible-lint, ruff, eslint)
	@echo "terraform fmt -check"; cd $(TF_DIR) && terraform fmt -check -recursive || true
	@echo "STATUS: ansible-lint / ruff / eslint not wired up yet — see ROADMAP.md"

.PHONY: test
test: ## Run all test suites
	@echo "STATUS: no test suites exist yet — see ROADMAP.md"
