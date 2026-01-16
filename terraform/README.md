# Azure AI Foundry Agents Audit - Terraform Infrastructure

This directory contains Terraform configuration for deploying the Azure AI Foundry Agents Audit infrastructure, aligned with the Bicep templates in the `/infra` directory.

## Overview

The Terraform configuration deploys the following Azure resources:

- **Resource Group**: Container for all Azure resources
- **Security**: User Assigned Managed Identity and Key Vault
- **Monitoring**: Log Analytics Workspace and Application Insights
- **Data**: Storage Account (with containers and tables) and Cosmos DB (audit-poc database with vendors/invoices/payments containers)
- **AI Services**: Azure AI Foundry Hub with GPT-4o and text-embedding-ada-002 models, AI Search, Document Intelligence, and AI Project
- **Platform**: Container Registry
- **Applications** (optional): MCP Container Apps deployed via Bicep template

**Note**: The App Service Plan and Container Apps are only deployed when using the `-DeployApps` flag, matching the Bicep structure.

## Hybrid Deployment Approach

This project uses a **hybrid Terraform + Bicep** deployment:
- **Terraform** deploys all core infrastructure (security, monitoring, data, AI services, platform)
- **Bicep** deploys the application layer (Container Apps) for optimal Azure Container Apps support

This approach provides:
- Terraform state management for infrastructure resources
- Native Azure support for Container Apps via Bicep
- Consistent deployment across both methods

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- An active Azure subscription

## Authentication

Authenticate to Azure using the Azure CLI:

```powershell
az login
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

## Configuration

### Automatic Configuration (with deploy-terraform.ps1)

The deployment script automatically creates the `terraform.tfvars` file for you.

### Manual Configuration

Create a `terraform.tfvars` file with the following variables:

```hcl
subscription_id  = "your-subscription-id"
environment_name = "demo"
project_name     = "audit"
resource_token   = "unique123"
location         = "eastus2"
```

### Optional Variables

```hcl
# Deploy MCP Container Apps
deploy_applications = false

# Custom OpenAI endpoint (if not using the deployed AI Foundry)
openai_endpoint = ""
```

### Variable Descriptions

- **subscription_id**: Your Azure subscription ID
- **environment_name**: Environment identifier (e.g., "demo", "dev", "prod") - between 1-64 characters
- **project_name**: Project identifier used in resource naming (default: "audit") - between 1-64 characters
- **resource_token**: Unique token for resource naming (e.g., build ID, commit hash)
- **location**: Azure region for deployment (e.g., "eastus2")
- **deploy_applications**: Set to `true` to include App Service Plan in Terraform deployment (Container Apps deployed via Bicep) (default: `false`)
- **openai_endpoint**: Custom Azure OpenAI endpoint (optional, uses deployed AI Foundry if not specified)

## Deployment

### Option 1: Using the PowerShell Deployment Script (Recommended)

The easiest way to deploy is using the provided PowerShell script from the project root:

```powershell
# Deploy infrastructure only 
.\deploy-terraform.ps1 -Subscription "YOUR_SUBSCRIPTION_NAME" -Location "eastus2"

# Deploy infrastructure and applications
.\deploy-terraform.ps1 -Subscription "YOUR_SUBSCRIPTION_NAME" -Location "eastus2" -DeployApps
```

The script will:
1. Generate a unique resource token
2. Login to Azure
3. Create terraform.tfvars automatically
4. Initialize, plan, and apply Terraform to deploy core infrastructure
5. Optionally build MCP container images (when `-DeployApps` is used)
6. Optionally deploy Container Apps via Bicep template (when `-DeployApps` is used)

### Option 2: Manual Terraform Deployment

#### Initialize Terraform

```powershell
cd terraform
terraform init
```

#### Plan Deployment

Review the resources that will be created:

```powershell
terraform plan
```

#### Apply Configuration

Deploy the infrastructure:

```powershell
terraform apply
```

Confirm the deployment by typing `yes` when prompted.

#### Deploy with Applications

To deploy including the web apps and function apps:

```powershell
terraform apply -var="deploy_applications=true"
```

## Module Structure

The Terraform configuration is organized to align with the Bicep structure in `/infra`:

```
terraform/
├── main.tf              # Main configuration and module orchestration
├── variables.tf         # Input variable definitions
├── outputs.tf           # Output value definitions
├── providers.tf         # Provider configurations
├── app/                 # Application resources (Web Apps, Function Apps, App Service Plan)
│   └── main.tf         # Aligns with /infra/app/
└── modules/             # Core infrastructure modules (aligns with /infra/core/)
    ├── security/        # Managed Identity and Key Vault
    ├── monitor/         # Log Analytics and Application Insights
    ├── data/            # Storage Account and Cosmos DB
    ├── ai/              # AI Foundry Hub, Models, and AI Project
    └── platform/        # Container Registry
```

### Structure Alignment with Bicep

The Terraform structure is now fully aligned with the Bicep templates:

- **modules/security** → `/infra/core/security/`
- **modules/monitor** → `/infra/core/monitor/`
- **modules/data** → `/infra/core/data/`
- **modules/ai** → `/infra/core/ai/`
- **modules/platform** → `/infra/core/platform/` (Container Registry)
- **app/** → `/infra/app/` (App Service Plan + Application deployment)

**Key Alignment**: App Service Plan is only deployed when applications are deployed, matching Bicep behavior.

## Outputs

After successful deployment, Terraform will output:

- **resource_group_name**: Name of the created resource group
- **managed_identity_name**: Name of the managed identity
- **storage_account_name**: Name of the storage account
- **log_analytics_workspace_name**: Name of the Log Analytics workspace
- **application_insights_name**: Name of Application Insights
- **openai_endpoint**: Azure OpenAI endpoint URL
- **ai_project_endpoint**: AI Project discovery endpoint
- **cosmosdb_endpoint**: Cosmos DB endpoint URL
- **container_registry_name**: Name of the Container Registry

If applications are deployed (`deploy_applications = true`):
- **app_service_plan_name**: Name of the App Service Plan
- **backend_web_app_url**: URL of the backend API
- **frontend_web_app_url**: URL of the frontend web application
- **function_app_name**: Name of the audio processing function app

## Access Outputs

View outputs after deployment:

```powershell
terraform output
```

View a specific output:

```powershell
terraform output backend_web_app_url
```

## Updating Infrastructure

To update the infrastructure with changes:

1. Modify the Terraform configuration files
2. Run `terraform plan` to review changes
3. Run `terraform apply` to apply changes

## Destroying Resources

To remove all created resources:

```powershell
terraform destroy
```

**Warning**: This will permanently delete all resources. Confirm by typing `yes` when prompted.

## Key Differences from Bicep

1. **Provider Configuration**: Terraform uses explicit provider blocks instead of Bicep's implicit Azure Resource Manager
2. **Module Syntax**: Terraform uses `module` blocks with `source` paths instead of Bicep's module references
3. **Resource Naming**: Some resources use `azurerm_*` for standard resources and `azapi_resource` for preview/newer Azure resources
4. **State Management**: Terraform maintains a state file (`terraform.tfstate`) to track resources
5. **Application Stack Configuration**: The syntax for configuring application stacks differs between providers

## State Management

The default configuration uses local state storage. For production deployments, consider using remote state storage (Azure Storage Account) by adding a backend configuration:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatestorage"
    container_name       = "tfstate"
    key                  = "aiagentvoice.terraform.tfstate"
  }
}
```

## Troubleshooting

### Permission Issues

Ensure your Azure account has the necessary permissions:
- Contributor role on the subscription or resource group
- User Access Administrator role (for role assignments)

### AI Services Deployment

The AI Foundry Hub and models may take 10-15 minutes to deploy. If you encounter quota issues, request quota increases in the Azure portal.

### Application Configuration

After deploying applications, you may need to:
1. Deploy application code using the deployment scripts in `/scripts`
2. Configure additional application settings
3. Set up custom domains and SSL certificates

## Additional Resources

- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [Original Bicep Templates](../infra/)

## Support

For issues related to:
- **Terraform Configuration**: Open an issue in this repository
- **Azure Resources**: Consult Azure documentation or support
- **Application Code**: Refer to the main project README

## License

See [LICENSE.md](../LICENSE.md) for license information.
