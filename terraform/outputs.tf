output "mcp_container_app_url" {
  description = "FQDN of the MCP Container App"
  value       = var.deploy_applications ? module.app[0].mcp_container_app_url : null
}
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "managed_identity_name" {
  description = "Name of the managed identity"
  value       = module.security.managed_identity_name
}

output "managed_identity_id" {
  description = "Resource ID of the managed identity"
  value       = module.security.managed_identity_id
}

output "container_registry_name" {
  description = "Name of the container registry"
  value       = module.platform.container_registry_name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = module.data.storage_account_name
}

output "log_analytics_workspace_name" {
  description = "Name of the Log Analytics workspace"
  value       = module.monitor.log_analytics_workspace_name
}

output "application_insights_name" {
  description = "Name of the Application Insights instance"
  value       = module.monitor.application_insights_name
}

output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = module.ai.openai_endpoint
}

output "ai_project_endpoint" {
  description = "AI Project endpoint"
  value       = module.ai.ai_project_endpoint
}

output "cosmosdb_endpoint" {
  description = "Cosmos DB endpoint"
  value       = module.data.cosmosdb_endpoint
}



