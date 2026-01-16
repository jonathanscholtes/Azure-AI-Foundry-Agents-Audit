variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "environment_name" {
  description = "Name representing the deployment environment (e.g., 'dev', 'test', 'prod', 'lab'); used to generate a short, unique hash for each resource"
  type        = string
  validation {
    condition     = length(var.environment_name) >= 1 && length(var.environment_name) <= 64
    error_message = "Environment name must be between 1 and 64 characters."
  }
}

variable "project_name" {
  description = "Name used to identify the project; also used to generate a short, unique hash for each resource"
  type        = string
  validation {
    condition     = length(var.project_name) >= 1 && length(var.project_name) <= 64
    error_message = "Project name must be between 1 and 64 characters."
  }
}

variable "resource_token" {
  description = "Token or string used to uniquely identify this resource deployment (e.g., build ID, commit hash)"
  type        = string
}

variable "location" {
  description = "Azure region where all resources will be deployed (e.g., 'eastus')"
  type        = string
  validation {
    condition     = length(var.location) >= 1
    error_message = "Location must not be empty."
  }
}

# Optional variables for application deployment
variable "openai_endpoint" {
  description = "Endpoint URL of the Azure OpenAI resource (e.g., https://your-resource.openai.azure.com/)"
  type        = string
  default     = ""
}

variable "deploy_applications" {
  description = "Whether to deploy the application components (web apps and function apps)"
  type        = bool
  default     = false
}
