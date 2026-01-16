param (
    [string]$Subscription,
    [string]$Location = "eastus2",
    [switch]$DeployApps = $false,
    [switch]$Destroy 
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Azure AI Foundry Agents - Terraform Deploy" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Subscription: $Subscription"
Write-Host "Location: $Location"
Write-Host "Deploy Applications: $DeployApps"
Write-Host ""

# Variables
$projectName = "audit"
$environmentName = "demo"
$timestamp = Get-Date -Format "yyyyMMddHHmmss"

function Get-RandomAlphaNumeric {
    param (
        [int]$Length = 12,
        [string]$Seed
    )

    $base62Chars = "abcdefghijklmnopqrstuvwxyz123456789"

    # Convert the seed string to a hash (e.g., MD5)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $seedBytes = [System.Text.Encoding]::UTF8.GetBytes($Seed)
    $hashBytes = $md5.ComputeHash($seedBytes)

    # Use bytes from hash to generate characters
    $randomString = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $index = $hashBytes[$i % $hashBytes.Length] % $base62Chars.Length
        $randomString += $base62Chars[$index]
    }

    return $randomString
}

# Generate resource token
$resourceToken = Get-RandomAlphaNumeric -Length 12 -Seed $timestamp

# Check if Terraform is installed
Write-Host "Checking Terraform installation..." -ForegroundColor Yellow
try {
    $terraformVersion = terraform version
    Write-Host "Terraform is installed" -ForegroundColor Green
    Write-Host $terraformVersion[0]
} catch {
    Write-Host "Terraform is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Terraform from: https://www.terraform.io/downloads.html"
    exit 1
}

# Clear account context and configure Azure CLI settings
Write-Host "`nConfiguring Azure CLI..." -ForegroundColor Yellow
az account clear
az config set core.enable_broker_on_windows=false
az config set core.login_experience_v2=off

# Login to Azure
Write-Host "`nLogging into Azure..." -ForegroundColor Yellow
az login 
az account set --subscription $Subscription

# Get subscription ID
$subscriptionId = az account show --query id -o tsv
Write-Host "Connected to subscription: $subscriptionId" -ForegroundColor Green


# Change to terraform directory
Set-Location -Path .\terraform

# If -Destroy is specified, run terraform destroy and exit
if ($Destroy.IsPresent) {
    Write-Host "\nDestroying all Terraform-managed resources..." -ForegroundColor Yellow
    terraform destroy -var-file="terraform.tfvars"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Terraform destroy failed" -ForegroundColor Red
        Set-Location -Path ..
        exit 1
    }
    Write-Host "All resources destroyed successfully." -ForegroundColor Green
    Set-Location -Path ..
    exit 0
}

# Create terraform.tfvars file
Write-Host "`nCreating terraform.tfvars..." -ForegroundColor Yellow

# First pass: always deploy infrastructure only (deploy_applications = false)
# This ensures ACR and other infrastructure exist before building images
$tfvarsContent = @"
subscription_id     = "$subscriptionId"
environment_name    = "$environmentName"
project_name        = "$projectName"
resource_token      = "$resourceToken"
location            = "$Location"
deploy_applications = false
"@

Set-Content -Path "terraform.tfvars" -Value $tfvarsContent
Write-Host "Created terraform.tfvars (infrastructure only)" -ForegroundColor Green

if ($DeployApps) {
    Write-Host "Note: Two-phase deployment - infrastructure first, then applications" -ForegroundColor Cyan
} else {
    Write-Host "Note: Core infrastructure only (no App Service Plan)" -ForegroundColor Cyan
}

# Initialize Terraform
Write-Host "`nInitializing Terraform..." -ForegroundColor Yellow
terraform init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Terraform initialization failed" -ForegroundColor Red
        Set-Location -Path ..
        exit 1
    }
    Write-Host "Terraform initialized" -ForegroundColor Green

    # Plan Terraform deployment
# Plan Terraform deployment
terraform plan -out=tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform plan failed" -ForegroundColor Red
    Set-Location -Path ..
    exit 1
}
Write-Host "Terraform plan created" -ForegroundColor Green

# Apply Terraform deployment
Write-Host "`nApplying Terraform configuration..." -ForegroundColor Yellow
Write-Host "This may take 10-15 minutes..." -ForegroundColor Cyan
terraform apply tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform apply failed" -ForegroundColor Red
    Set-Location -Path ..
    exit 1
}
Write-Host "Infrastructure deployed successfully" -ForegroundColor Green

# Get Terraform outputs
Write-Host "`nRetrieving deployment outputs..." -ForegroundColor Yellow
$terraformOutputJson = terraform output -json | ConvertFrom-Json

$resourceGroupName = $terraformOutputJson.resource_group_name.value
$managedIdentityName = $terraformOutputJson.managed_identity_name.value
$storageAccountName = $terraformOutputJson.storage_account_name.value
$applicationInsightsName = $terraformOutputJson.application_insights_name.value

Write-Host "Resource Group: $resourceGroupName" -ForegroundColor Cyan
Write-Host "Managed Identity: $managedIdentityName" -ForegroundColor Cyan
Write-Host "Storage Account: $storageAccountName" -ForegroundColor Cyan

# Build MCP Container Images if deploying apps
if ($DeployApps) {
    $containerRegistryName = $terraformOutputJson.container_registry_name.value
    
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "Building MCP Container Images" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Using ACR: $containerRegistryName" -ForegroundColor Cyan
    Write-Host "Resource Group: $resourceGroupName`n" -ForegroundColor Cyan

    # Define image names and paths
    $images = @(
        @{ name = "audit-mcp"; path = "..\src\MCP\audit" }
    )

    # Build images
    foreach ($image in $images) {
        Write-Host "Building image '$($image.name):latest' from '$($image.path)'..." -ForegroundColor Yellow
        
        az acr build `
            --resource-group $resourceGroupName `
            --registry $containerRegistryName `
            --image "$($image.name):latest" `
            $image.path
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to build image '$($image.name)'" -ForegroundColor Red
            Set-Location -Path ..
            exit 1
        }
        Write-Host " Image '$($image.name):latest' built successfully" -ForegroundColor Green
    }

    # Deploy MCP Container Apps using Terraform (not Bicep)
    Write-Host "`n==========================================" -ForegroundColor Cyan
    Write-Host "Deploying Container Apps (Phase 2)" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    
    # Update terraform.tfvars to enable application deployment
    Write-Host "Updating terraform.tfvars to enable application deployment..." -ForegroundColor Yellow
    $tfvarsContent = @"
subscription_id     = "$subscriptionId"
environment_name    = "$environmentName"
project_name        = "$projectName"
resource_token      = "$resourceToken"
location            = "$Location"
deploy_applications = true
"@
    Set-Content -Path "terraform.tfvars" -Value $tfvarsContent
    Write-Host "Updated terraform.tfvars (deploy_applications = true)" -ForegroundColor Green
    
    Write-Host "`nRunning Terraform plan to deploy Container Apps..." -ForegroundColor Yellow
    terraform plan -out=tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Terraform plan (second pass) failed" -ForegroundColor Red
        Set-Location -Path ..
        exit 1
    }
    
    Write-Host "`nApplying Terraform configuration to deploy Container Apps..." -ForegroundColor Yellow
    terraform apply tfplan
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Terraform apply (second pass) failed" -ForegroundColor Red
        Set-Location -Path ..
        exit 1
    }
    Write-Host "Container Apps deployed successfully via Terraform." -ForegroundColor Green
} else {
    Write-Host "`nContainer Apps deployment skipped. Use -DeployApps flag to deploy applications." -ForegroundColor Yellow
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "`nDeployed Resources:" -ForegroundColor Cyan
Write-Host "Resource Group: $resourceGroupName" -ForegroundColor Cyan
Write-Host "Key Vault: $($terraformOutputJson.key_vault_name.value)" -ForegroundColor Cyan
Write-Host "Storage Account: $($terraformOutputJson.storage_account_name.value)" -ForegroundColor Cyan
Write-Host "Cosmos DB: $($terraformOutputJson.cosmosdb_endpoint.value)" -ForegroundColor Cyan
Write-Host "Container Registry: $($terraformOutputJson.container_registry_name.value)" -ForegroundColor Cyan

if ($DeployApps) {
    Write-Host "`nMCP Container Apps deployed successfully" -ForegroundColor Green
    $mcpContainerAppUrl = $terraformOutputJson.mcp_container_app_url.value
    if ($mcpContainerAppUrl) {
        Write-Host "MCP Container App URL: https://$mcpContainerAppUrl" -ForegroundColor Cyan
    }
}

Write-Host "\nTo view all outputs, run: cd terraform; terraform output" -ForegroundColor Yellow
Write-Host "To destroy resources, run: .\deploy-terraform.ps1 -Subscription \"$Subscription\" -Destroy" -ForegroundColor Yellow
Write-Host "\nFor more information, see: terraform/README.md" -ForegroundColor Cyan
