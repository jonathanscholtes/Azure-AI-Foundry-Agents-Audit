variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment_name" {
  description = "Environment name"
  type        = string
}

variable "resource_token" {
  description = "Resource token"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "managed_identity_principal_id" {
  description = "Principal ID of the managed identity"
  type        = string
}

locals {
  container_registry_name = "cr${var.project_name}${var.environment_name}${var.resource_token}"
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = local.container_registry_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Basic"
  admin_enabled       = true
}

# Grant managed identity AcrPull role on the container registry
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = var.managed_identity_principal_id
}

output "container_registry_name" {
  value       = azurerm_container_registry.main.name
  description = "Name of the container registry"
}

output "container_registry_id" {
  value       = azurerm_container_registry.main.id
  description = "Resource ID of the container registry"
}

output "container_registry_login_server" {
  value       = azurerm_container_registry.main.login_server
  description = "Login server URL of the container registry"
}
