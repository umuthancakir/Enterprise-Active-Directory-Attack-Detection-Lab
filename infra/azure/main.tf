# infra/azure/main.tf
#
# Resource group + admin credential generation. Everything the lab creates
# lives inside azurerm_resource_group.lab, so `make down` (terraform destroy)
# reliably tears down the whole environment in one pass — see
# docs/adr/0003-azure-network-isolation.md and SECURITY.md #4 (ephemeral).

resource "azurerm_resource_group" "lab" {
  name     = var.resource_group_name
  location = var.region
  tags     = var.tags
}

# Synthetic admin credential (SECURITY.md #5: no real secrets). Generated
# unless the operator supplies var.admin_password explicitly via
# TF_VAR_admin_password or a gitignored .tfvars file.
resource "random_password" "admin" {
  count       = var.admin_password == null ? 1 : 0
  length      = 24
  special     = true
  min_upper   = 2
  min_lower   = 2
  min_numeric = 2
  min_special = 2
}

locals {
  admin_password = coalesce(var.admin_password, try(random_password.admin[0].result, null))
}

# Linux hosts (attacker, SIEM) use key-based SSH auth rather than password
# auth — least-privilege default even though these are lab hosts reachable
# only via Bastion (docs/adr/0003-azure-network-isolation.md).
resource "tls_private_key" "linux_ssh" {
  algorithm = "ED25519"
}

