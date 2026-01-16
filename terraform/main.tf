# Generate unique resource token if not provided
resource "random_string" "resource_token" {
  length  = 8
  special = false
  upper   = false
  lower   = true
  numeric = true
}

locals {
  resource_token      = var.resource_token != "" ? var.resource_token : random_string.resource_token.result
  resource_group_name = "rg-${var.project_name}-${var.environment_name}-${var.location}-${local.resource_token}"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
}

# Security Module (Key Vault, Managed Identity)
module "security" {
  source = "./modules/security"

  key_vault_name        = "kv${var.project_name}${local.resource_token}"
  managed_identity_name = "id-${var.project_name}-${var.environment_name}"
  location              = var.location
  resource_group_name   = azurerm_resource_group.main.name
}

# Monitoring Module (Log Analytics, Application Insights)
module "monitor" {
  source = "./modules/monitor"

  location                  = var.location
  resource_group_name       = azurerm_resource_group.main.name
  log_analytics_name        = "log-${var.project_name}-${var.environment_name}-${local.resource_token}"
  application_insights_name = "appi-${var.project_name}-${var.environment_name}-${local.resource_token}"
}

# Data Module (Storage Account, Cosmos DB)
module "data" {
  source = "./modules/data"

  project_name          = var.project_name
  resource_token        = local.resource_token
  environment_name      = var.environment_name
  location              = var.location
  resource_group_name   = azurerm_resource_group.main.name
  identity_id           = module.security.managed_identity_id
  identity_principal_id = module.security.managed_identity_principal_id
}

# AI Module (AI Foundry)
module "ai" {
  source = "./modules/ai"

  project_name          = var.project_name
  environment_name      = var.environment_name
  resource_token        = local.resource_token
  location              = var.location
  resource_group_name   = azurerm_resource_group.main.name
  app_insights_name     = module.monitor.application_insights_name
  app_insights_id       = module.monitor.application_insights_id
  identity_id           = module.security.managed_identity_id
  identity_principal_id = module.security.managed_identity_principal_id
  storage_account_id    = module.data.storage_account_id
}

# Platform Module (Container Registry)
module "platform" {
  source = "./modules/platform"

  project_name                = var.project_name
  environment_name            = var.environment_name
  resource_token              = local.resource_token
  location                    = var.location
  resource_group_name         = azurerm_resource_group.main.name
  managed_identity_principal_id = module.security.managed_identity_principal_id
}

# App Module (App Service Plan, Web Apps and Function Apps)
module "app" {
  count  = var.deploy_applications ? 1 : 0
  source = "./modules/app"

  project_name                 = var.project_name
  environment_name             = var.environment_name
  resource_token               = local.resource_token
  location                     = var.location
  resource_group_name          = azurerm_resource_group.main.name
  managed_identity_id          = module.security.managed_identity_id
  log_analytics_workspace_name = module.monitor.log_analytics_workspace_name
  app_insights_name            = module.monitor.application_insights_name
  key_vault_uri                = module.security.key_vault_uri
  cosmosdb_endpoint            = module.data.cosmosdb_endpoint
  container_registry_login_server = module.platform.container_registry_login_server

  depends_on = [
    module.platform,
    module.monitor,
    module.security,
    module.data,
    module.ai
  ]
}
