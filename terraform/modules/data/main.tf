
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

locals {
  storage_account_name = "sa${var.project_name}${var.resource_token}"
  cosmos_account_name  = "cosmos-${var.project_name}-${var.environment_name}-${var.resource_token}"
}

variable "identity_id" {
  description = "Resource ID of the managed identity"
  type        = string
}

variable "identity_principal_id" {
  description = "Principal ID of the managed identity"
  type        = string
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = local.storage_account_name
  location                 = var.location
  resource_group_name      = var.resource_group_name
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"


  # Enable hierarchical namespace for Data Lake Gen2
  is_hns_enabled = false

  # Enforce RBAC, disable key-based authentication
  shared_access_key_enabled = false
}

# Storage Containers
resource "azurerm_storage_container" "containers" {
  for_each = toset(["load", "processed"])

  name                  = each.key
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}



# Grant Storage Blob Data Contributor role to managed identity
resource "azurerm_role_assignment" "blob_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.identity_principal_id
}

# Grant Storage Table Data Contributor role to managed identity
resource "azurerm_role_assignment" "table_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = var.identity_principal_id
}

# Grant Storage Account Contributor role to managed identity
resource "azurerm_role_assignment" "account_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Account Contributor"
  principal_id         = var.identity_principal_id
}

# Grant Storage Blob Data Owner role to managed identity
resource "azurerm_role_assignment" "blob_owner" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = var.identity_principal_id
}

# Grant Storage Queue Data Contributor role to managed identity
resource "azurerm_role_assignment" "queue_contributor" {
  scope                = azurerm_storage_account.main.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = var.identity_principal_id
}

# Cosmos DB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = local.cosmos_account_name
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }
}

# Cosmos DB Database
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "audit-poc"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Cosmos DB Containers
resource "azurerm_cosmosdb_sql_container" "vendors" {
  name                = "vendors"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/engagement_id"]
  default_ttl         = 0

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/engagement_id/?"
    }

    excluded_path {
      path = "/*"
    }
  }
}

resource "azurerm_cosmosdb_sql_container" "invoices" {
  name                = "invoices"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/engagement_id"]
  default_ttl         = 0

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/engagement_id/?"
    }

    excluded_path {
      path = "/*"
    }
  }
}

resource "azurerm_cosmosdb_sql_container" "payments" {
  name                = "payments"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/engagement_id"]
  default_ttl         = 0

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/engagement_id/?"
    }

    excluded_path {
      path = "/*"
    }
  }
}

# Grant Cosmos DB Data Contributor role to managed identity
resource "azurerm_role_assignment" "cosmos_contributor" {
  scope                = azurerm_cosmosdb_account.main.id
  role_definition_name = "Cosmos DB Account Reader Role"
  principal_id         = var.identity_principal_id
}

# Grant Built-in Data Contributor role to managed identity (for data plane access)
resource "azurerm_cosmosdb_sql_role_assignment" "data_contributor" {
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.main.name
  role_definition_id  = "${azurerm_cosmosdb_account.main.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id        = var.identity_principal_id
  scope               = azurerm_cosmosdb_account.main.id
}

output "storage_account_id" {
  value = azurerm_storage_account.main.id
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "cosmosdb_endpoint" {
  value = azurerm_cosmosdb_account.main.endpoint
}

output "cosmosdb_id" {
  value = azurerm_cosmosdb_account.main.id
}
