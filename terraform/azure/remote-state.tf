terraform {
  backend "azurerm" {
    storage_account_name = "abaltratfstorage"
    container_name       = "tfstates"
    key                  = "velkoz-core/terraform.tfstate"
    resource_group_name  = "terraform"
  }
}