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

variable "managed_identity_id" {
description = "Resource ID of the managed identity"
type        = string
}

variable "log_analytics_workspace_name" {
description = "Name of the Log Analytics workspace"
type        = string
}

variable "key_vault_uri" {
description = "URI of the Key Vault"
type        = string
}

variable "cosmosdb_endpoint" {
description = "Cosmos DB endpoint"
type        = string
}

variable "container_registry_login_server" {
description = "Login server URL of the container registry"
type        = string
}


variable "app_insights_name" {
  description = "Name of Application Insights"
  type        = string
}



data "azurerm_log_analytics_workspace" "main" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.resource_group_name
}

data "azurerm_user_assigned_identity" "main" {
  name                = split("/", var.managed_identity_id)[8]
  resource_group_name = var.resource_group_name
}

data "azurerm_application_insights" "main" {
  name                = var.app_insights_name
  resource_group_name = var.resource_group_name
}


# Container App Environment
resource "azurerm_container_app_environment" "mcp" {
  name                = "cae-${var.project_name}-${var.environment_name}-${var.resource_token}"
  location            = var.location
  resource_group_name = var.resource_group_name
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.main.id
}



# MCP Container App
resource "azurerm_container_app" "mcp" {
  name                = "mcp-${var.project_name}-${var.environment_name}-${var.resource_token}"
  container_app_environment_id = azurerm_container_app_environment.mcp.id
  resource_group_name = var.resource_group_name

  identity {
    type         = "UserAssigned"
    identity_ids = [var.managed_identity_id]
  }

  revision_mode = "Single"

  template {
    container {
      name   = "audit"
      image  = "${var.container_registry_login_server}/audit-mcp:latest"
      cpu    = 0.5
      memory = "1.0Gi"
      env {
        name  = "SERVICE_NAME"
        value = "audit"
      }
      env {
        name  = "MCP_PORT"
        value = "80"
      }
      env {
        name  = "COSMOS_ENDPOINT"
        value = var.cosmosdb_endpoint
      }
      env {
        name  = "COSMOS_DATABASE"
        value = "audit-poc"
      }
      env {
        name  = "COSMOS_CONTAINER"
        value = ""
      }
      env {
        name  = "AZURE_CLIENT_ID"
        value = data.azurerm_user_assigned_identity.main.client_id
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }


  registry {
    server   = var.container_registry_login_server
    identity = var.managed_identity_id
  }
}

output "mcp_container_app_url" {
  value       = azurerm_container_app.mcp.latest_revision_fqdn 
  description = "FQDN of the MCP Container App"
}
