
terraform {
  required_providers {
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
  }
}

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

variable "app_insights_name" {
  description = "Name of Application Insights"
  type        = string
}

variable "app_insights_id" {
  description = "Resource ID of Application Insights"
  type        = string
}

variable "identity_id" {
  description = "Resource ID of the managed identity"
  type        = string
}

variable "identity_principal_id" {
  description = "Principal ID of the managed identity"
  type        = string
}

variable "storage_account_id" {
  description = "Resource ID of the storage account"
  type        = string
}

locals {
  ai_account_name = "fnd-${var.project_name}-${var.environment_name}-${var.resource_token}"
  ai_project_name = "proj-${var.project_name}-${var.environment_name}-${var.resource_token}"
}

data "azurerm_client_config" "current" {}

# AI Services Account (Microsoft Foundry )
resource "azapi_resource" "ai_account" {
  type      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name      = local.ai_account_name
  location  = var.location
  parent_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${var.resource_group_name}"

  identity {
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }

  body = {
    kind = "AIServices"
    properties = {
      apiProperties       = {}
      customSubDomainName = local.ai_account_name
      networkAcls = {
        defaultAction       = "Allow"
        virtualNetworkRules = []
        ipRules             = []
      }
      allowProjectManagement = true
      publicNetworkAccess    = "Enabled"
      disableLocalAuth       = false
    }
    sku = {
      name = "S0"
    }
    tags = {
      "SecurityControl" = "ignore"
    }
  }
}


# GPT-4o deployment
resource "azapi_resource" "gpt4o_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "gpt-4o"
  parent_id = azapi_resource.ai_account.id
  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 250
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-4o"
        version = "2024-11-20"
      }
      versionUpgradeOption = "OnceCurrentVersionExpired"
      raiPolicyName = "Microsoft.DefaultV2"
    }
  }
}

# GPT-5.2-chat deployment
resource "azapi_resource" "gpt52_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "gpt-5.2-chat"
  parent_id = azapi_resource.ai_account.id
  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 150
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-5.2-chat"
        version = "2025-12-11"
      }
      versionUpgradeOption = "OnceNewDefaultVersionAvailable"
      raiPolicyName = "Microsoft.DefaultV2"
    }
  }
  depends_on = [azapi_resource.gpt4o_deployment]
}

# o3-mini deployment
resource "azapi_resource" "o3mini_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "o3-mini"
  parent_id = azapi_resource.ai_account.id
  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 250
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "o3-mini"
        version = "2025-01-31"
      }
      versionUpgradeOption = "OnceCurrentVersionExpired"
      raiPolicyName = "Microsoft.DefaultV2"
    }
  }
  depends_on = [azapi_resource.gpt52_deployment]
}

# text-embedding-3-large deployment
resource "azapi_resource" "embedding_deployment" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2025-06-01"
  name      = "text-embedding-3-large"
  parent_id = azapi_resource.ai_account.id
  body = {
    sku = {
      name     = "Standard"
      capacity = 120
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "text-embedding-3-large"
        version = "1"
      }
      versionUpgradeOption = "OnceCurrentVersionExpired"
      raiPolicyName = "Microsoft.DefaultV2"
    }
  }
  depends_on = [azapi_resource.o3mini_deployment]
}

# AI Project
resource "azapi_resource" "ai_project" {
  type      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name      = local.ai_project_name
  location  = var.location
  parent_id = azapi_resource.ai_account.id

  identity {
    type = "SystemAssigned"
  }

  body = {
    properties = {}
  }

  depends_on = [
    azapi_resource.ai_account,
    azapi_resource.gpt4o_deployment,
    azapi_resource.embedding_deployment
  ]
}

# Grant Cognitive Services OpenAI User role to managed identity
resource "azurerm_role_assignment" "openai_user" {
  scope                = azapi_resource.ai_account.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = var.identity_principal_id
}

# Grant Cognitive Services User role to managed identity
resource "azurerm_role_assignment" "cognitive_services_user" {
  scope                = azapi_resource.ai_account.id
  role_definition_name = "Cognitive Services User"
  principal_id         = var.identity_principal_id
}

output "ai_account_endpoint" {
  value = azapi_resource.ai_account.output.properties.endpoint
}

output "ai_services_target" {
  value = azapi_resource.ai_account.id
}

output "openai_endpoint" {
  value = "https://${local.ai_account_name}.cognitiveservices.azure.com/"
}

output "ai_project_endpoint" {
  value = azapi_resource.ai_project.output.properties.endpoints["AI Foundry API"]
}

output "ai_account_id" {
  value = azapi_resource.ai_account.id
}

output "ai_project_id" {
  value = azapi_resource.ai_project.id
}
