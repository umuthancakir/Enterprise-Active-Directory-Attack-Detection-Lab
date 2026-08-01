# infra/azure/siem.tf
#
# SIEM host (Ubuntu 22.04 LTS). Elastic/Wazuh install and telemetry ingest
# config is handled by config/siem/ and telemetry/ — not written yet, see
# ROADMAP.md Phase 2. This is a telemetry sink only, never a valid attack
# target — see inventory/lab-scope.yaml's non_attackable_roles.

resource "azurerm_network_interface" "siem" {
  name                = "${var.lab_name}-siem01-nic"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.lab.id
    private_ip_address_allocation = "Static"
    private_ip_address            = cidrhost(var.lab_subnet_prefix, 20)
  }
}

resource "azurerm_linux_virtual_machine" "siem" {
  name                            = "siem01"
  computer_name                   = "siem01"
  location                        = azurerm_resource_group.lab.location
  resource_group_name             = azurerm_resource_group.lab.name
  size                            = var.vm_sizes["siem"]
  admin_username                  = var.admin_username
  disable_password_authentication = true
  tags                            = var.tags

  admin_ssh_key {
    username   = var.admin_username
    public_key = tls_private_key.linux_ssh.public_key_openssh
  }

  network_interface_ids = [azurerm_network_interface.siem.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
    disk_size_gb         = 128 # headroom for Elastic/Wazuh indices during scenario runs
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}
