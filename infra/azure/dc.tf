# infra/azure/dc.tf
#
# Domain Controller VM. Terraform provisions the VM itself; promoting it to
# a domain controller, creating the forest/domain, and configuring the
# synthetic OU/user/group structure and deliberate misconfigurations
# (docs/vulnerabilities.md) is done by the config/dc/ Ansible role — that
# role is not written yet, see ROADMAP.md Phase 1.

resource "azurerm_network_interface" "dc" {
  name                = "${var.lab_name}-dc01-nic"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.lab.id
    private_ip_address_allocation = "Static"
    private_ip_address            = cidrhost(var.lab_subnet_prefix, 4)
  }
}

resource "azurerm_windows_virtual_machine" "dc" {
  name                = "dc01"
  computer_name        = "DC01"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  size                = var.vm_sizes["dc"]
  admin_username      = var.admin_username
  admin_password      = local.admin_password
  tags                = var.tags

  network_interface_ids = [azurerm_network_interface.dc.id]

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
}
