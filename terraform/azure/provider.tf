provider "azurerm" {
  # Whilst version is optional, we /strongly recommend/ using it to pin the version of the Provider being used
  version = "=1.44.0"
}

#create resource group
resource "azurerm_resource_group" "rg" {
    name     = "rg-velkoz"
    location = "eastus"
}