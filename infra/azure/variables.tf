variable "azure_subscription_id" {
  description = "Azure subscription to deploy into. Required — see .env.example AZURE_SUBSCRIPTION_ID."
  type        = string
}

variable "region" {
  description = "Azure region for the lab resource group."
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the isolated resource group that contains every lab resource. `make down` = destroy this group's contents."
  type        = string
  default     = "eadadl-lab-rg"
}

variable "lab_name" {
  description = "Short name used as a prefix for lab resources and DNS. Must match inventory/lab-scope.yaml's lab.name."
  type        = string
  default     = "eadadl"
}

variable "vnet_address_space" {
  description = "Address space for the isolated lab vnet. Never routed to the internet — see docs/adr/0003-azure-network-isolation.md."
  type        = list(string)
  default     = ["10.42.0.0/16"]
}

variable "lab_subnet_prefix" {
  description = "Subnet for all lab hosts (DC, members, workstation, attacker, SIEM)."
  type        = string
  default     = "10.42.1.0/24"
}

variable "bastion_subnet_prefix" {
  description = "AzureBastionSubnet — name and /26-or-larger size are required by Azure Bastion."
  type        = string
  default     = "10.42.2.0/26"
}

variable "operator_source_ips" {
  description = "CIDR ranges allowed to reach Azure Bastion's public IP (HTTPS/443). Set to your own IP, not 0.0.0.0/0."
  type        = list(string)
}

variable "domain_name" {
  description = "AD DNS domain name for the lab forest."
  type        = string
  default     = "eadadl.lab"
}

variable "domain_netbios_name" {
  description = "NetBIOS name for the lab domain."
  type        = string
  default     = "EADADL"
}

variable "admin_username" {
  description = "Local admin / domain admin username for lab hosts. Synthetic only — see SECURITY.md #5."
  type        = string
  default     = "labadmin"
}

variable "admin_password" {
  description = "Admin password for lab hosts. Provide via TF_VAR_admin_password or a .tfvars file that is gitignored — never commit a real value. If unset, a random one is generated (see random_password.admin in main.tf)."
  type        = string
  default     = null
  sensitive   = true
}

variable "vm_sizes" {
  description = "VM SKU per role. Small/burstable by default to bound cost for a lab that's torn down between sessions."
  type        = map(string)
  default = {
    dc          = "Standard_B2ms"
    member      = "Standard_B2s"
    workstation = "Standard_B2s"
    attacker    = "Standard_B2s"
    siem        = "Standard_B2ms" # SIEM stack (Elastic/Wazuh) is the most memory-hungry host
  }
}

variable "tags" {
  description = "Common tags applied to every resource."
  type        = map(string)
  default = {
    project     = "eadadl"
    environment = "lab"
    managed_by  = "terraform"
  }
}
