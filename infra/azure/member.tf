# infra/azure/member.tf
#
# Domain-joined member server. Domain join and role-specific config (and any
# deliberate misconfigurations placed here rather than on the DC) are
# handled by config/member/ — not written yet, see ROADMAP.md Phase 1.

resource "azurerm_network_interface" "member" {
  name                = "${var.lab_name}-mem01-nic"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.lab.id
    private_ip_address_allocation = "Static"
    private_ip_address            = cidrhost(var.lab_subnet_prefix, 5)
  }
}

resource "azurerm_windows_virtual_machine" "member" {
  name                = "mem01"
  computer_name       = "MEM01"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  size                = var.vm_sizes["member"]
  admin_username      = var.admin_username
  admin_password      = local.admin_password
  tags                = var.tags

  network_interface_ids = [azurerm_network_interface.member.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
  }

  source_image_reference {
    publisher = "MicrosoftWindowsServer"
    offer     = "WindowsServer"
    sku       = "2022-datacenter-g2"
    version   = "latest"
  }

  depends_on = [azurerm_windows_virtual_machine.dc]
}
