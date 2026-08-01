terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Local state for this single-operator lab. Revisit (azurerm backend with
  # a storage account) if multi-operator use ever becomes a real need — see
  # docs/adr/0001-deploy-target.md for the single-operator framing.
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    virtual_machine {
      delete_os_disk_on_deletion     = true
      graceful_shutdown               = false
      skip_shutdown_and_force_delete  = false
    }
  }

  subscription_id = var.azure_subscription_id
}
