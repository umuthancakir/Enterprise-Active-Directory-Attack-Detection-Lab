# infra/azure/outputs.tf
#
# scripts/sync_scope.py reads `terraform output -json` and writes the
# resulting IPs/provisioned state into inventory/lab-scope.yaml — this is
# the mechanism ADR 0002 relies on to keep the scope guard's allow-list in
# sync with what's actually deployed. Keep output names matching the `id`
# fields in inventory/lab-scope.yaml's hosts list.

output "resource_group_name" {
  value = azurerm_resource_group.lab.name
}

output "region" {
  value = azurerm_resource_group.lab.location
}

output "hosts" {
  description = "Map of lab-scope host id -> private IP + provisioned state, consumed by scripts/sync_scope.py."
  value = {
    dc01 = {
      ip          = azurerm_network_interface.dc.private_ip_address
      provisioned = true
    }
    mem01 = {
      ip          = azurerm_network_interface.member.private_ip_address
      provisioned = true
    }
    wks01 = {
      ip          = azurerm_network_interface.workstation.private_ip_address
      provisioned = true
    }
    attacker01 = {
      ip          = azurerm_network_interface.attacker.private_ip_address
      provisioned = true
    }
    siem01 = {
      ip          = azurerm_network_interface.siem.private_ip_address
      provisioned = true
    }
  }
}

output "bastion_host_name" {
  value = azurerm_bastion_host.lab.name
}

output "admin_username" {
  value = var.admin_username
}

output "admin_password" {
  description = "Windows local admin / domain admin password (dc01, mem01, wks01)."
  value       = local.admin_password
  sensitive   = true
}

output "linux_ssh_private_key" {
  description = "SSH private key for attacker01/siem01 (var.admin_username). Retrieve with: terraform output -raw linux_ssh_private_key > eadadl-lab.pem && chmod 600 eadadl-lab.pem"
  value       = tls_private_key.linux_ssh.private_key_openssh
  sensitive   = true
}
