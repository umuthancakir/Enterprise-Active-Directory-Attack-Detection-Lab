# infra/azure/workstation.tf
#
# Domain-joined Windows 11 workstation — the typical "user endpoint" target
# for phishing/initial-access style techniques later in attack/. Domain
# join and any workstation-side misconfiguration is handled by
# config/workstation/ — not written yet, see ROADMAP.md Phase 1.

resource "azurerm_network_interface" "workstation" {
  name                = "${var.lab_name}-wks01-nic"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.lab.id
    private_ip_address_allocation = "Static"
    private_ip_address            = cidrhost(var.lab_subnet_prefix, 6)
  }
}

resource "azurerm_windows_virtual_machine" "workstation" {
  name                = "wks01"
  computer_name       = "WKS01"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  size                = var.vm_sizes["workstation"]
  admin_username      = var.admin_username
  admin_password      = local.admin_password
  tags                = var.tags

  network_interface_ids = [azurerm_network_interface.workstation.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
  }

  source_image_reference {
    publisher = "MicrosoftWindowsDesktop"
    offer     = "Windows-11"
    sku       = "win11-23h2-pro"
    version   = "latest"
  }

  depends_on = [azurerm_windows_virtual_machine.dc]
}
