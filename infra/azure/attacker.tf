# infra/azure/attacker.tf
#
# Attacker box (Kali Linux marketplace image). This is the ONLY host the
# attack/ engine invokes offensive tooling FROM — see
# inventory/lab-scope.yaml's non_attackable_roles and docs/adr/0002.
#
# Kali's marketplace image requires accepting Azure Marketplace terms once
# per subscription before it can be deployed; azurerm_marketplace_agreement
# does that idempotently as part of `terraform apply`.

resource "azurerm_marketplace_agreement" "kali" {
  publisher = "kali-linux"
  offer     = "kali"
  plan      = "kali"
}

resource "azurerm_network_interface" "attacker" {
  name                = "${var.lab_name}-attacker01-nic"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = var.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.lab.id
    private_ip_address_allocation = "Static"
    private_ip_address            = cidrhost(var.lab_subnet_prefix, 10)
  }
}

resource "azurerm_linux_virtual_machine" "attacker" {
  name                            = "attacker01"
  computer_name                   = "attacker01"
  location                        = azurerm_resource_group.lab.location
  resource_group_name             = azurerm_resource_group.lab.name
  size                            = var.vm_sizes["attacker"]
  admin_username                  = var.admin_username
  disable_password_authentication = true
  tags                            = var.tags

  admin_ssh_key {
    username   = var.admin_username
    public_key = tls_private_key.linux_ssh.public_key_openssh
  }

  network_interface_ids = [azurerm_network_interface.attacker.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "StandardSSD_LRS"
  }

  source_image_reference {
    publisher = "kali-linux"
    offer     = "kali"
    sku       = "kali"
    version   = "latest"
  }

  plan {
    name      = "kali"
    publisher = "kali-linux"
    product   = "kali"
  }

  depends_on = [azurerm_marketplace_agreement.kali]
}
