# infra/azure/network.tf
#
# Isolation model: see docs/adr/0003-azure-network-isolation.md. Summary —
# no lab host has a public IP or a route to the internet; the only inbound
# path is Azure Bastion (bastion.tf), restricted to var.operator_source_ips.

resource "azurerm_virtual_network" "lab" {
  name                = "${var.lab_name}-vnet"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  address_space       = var.vnet_address_space
  tags                = var.tags
}

resource "azurerm_subnet" "lab" {
  name                 = "lab-subnet"
  resource_group_name  = azurerm_resource_group.lab.name
  virtual_network_name = azurerm_virtual_network.lab.name
  address_prefixes     = [var.lab_subnet_prefix]
}

# Name is fixed by Azure — Bastion only works in a subnet named exactly this.
resource "azurerm_subnet" "bastion" {
  name                 = "AzureBastionSubnet"
  resource_group_name  = azurerm_resource_group.lab.name
  virtual_network_name = azurerm_virtual_network.lab.name
  address_prefixes     = [var.bastion_subnet_prefix]
}

resource "azurerm_network_security_group" "lab" {
  name                = "${var.lab_name}-lab-nsg"
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = var.tags

  # Deny all inbound from the internet. Only Bastion (below) and
  # intra-vnet traffic are allowed in.
  security_rule {
    name                       = "deny-inbound-internet"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "Internet"
    destination_address_prefix = "*"
  }

  # Deny all outbound to the internet. This is the enforcement point for
  # SECURITY.md invariant #1 — lab hosts never reach out beyond the vnet
  # (the Azure platform channel 168.63.129.16 is separate from this and is
  # not internet-routable; see docs/adr/0003-azure-network-isolation.md).
  security_rule {
    name                       = "deny-outbound-internet"
    priority                   = 4096
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }

  # Allow RDP/WinRM from the Bastion subnet only, for Ansible provisioning
  # and interactive access to Windows hosts.
  security_rule {
    name                       = "allow-bastion-windows-mgmt"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["3389", "5985", "5986"]
    source_address_prefix      = var.bastion_subnet_prefix
    destination_address_prefix = "*"
  }

  # Allow SSH from the Bastion subnet only, for the attacker box and SIEM
  # host (both Linux).
  security_rule {
    name                       = "allow-bastion-ssh"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.bastion_subnet_prefix
    destination_address_prefix = "*"
  }

  # Intra-lab traffic (AD/Kerberos/SMB/WinRM between hosts, attacker ->
  # targets, hosts -> SIEM shipping) — full mesh within the subnet. Scoping
  # this down port-by-port is tracked as a Phase 1 hardening follow-up once
  # the actual port matrix (Kerberos 88, LDAP 389/636, SMB 445, WinRM 5985,
  # Beats/Elastic 9200/5044, etc.) is finalized against real config/ roles.
  security_rule {
    name                       = "allow-intra-lab"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }
}

resource "azurerm_subnet_network_security_group_association" "lab" {
  subnet_id                 = azurerm_subnet.lab.id
  network_security_group_id = azurerm_network_security_group.lab.id
}
