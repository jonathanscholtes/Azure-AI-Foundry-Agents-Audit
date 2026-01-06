@description('Name used to identify the project; also used to generate a short, unique hash for each resource')
param projectName string

@description('Name representing the deployment environment (e.g., "dev", "test", "prod", "lab"); used to generate a short, unique hash for each resource')
param environmentName string

@description('Token or string used to uniquely identify this resource deployment (e.g., build ID, commit hash)')
param resourceToken string

@description('Azure region where all resources will be deployed (e.g., "eastus")')
param location string

@description('Name of the User Assigned Managed Identity to assign to deployed services')
param identityName string


module docIntelligence 'doc-account.bicep' = {
  name: 'docIntelligenceAccount'
  params: {
    accountName: 'docint-${projectName}-${environmentName}-${resourceToken}'
    location: location
    identityName: identityName
  }
}

output docIntelligenceAccountName string = docIntelligence.outputs.docIntelligenceAccountName
output docIntelligenceEndPoint string = docIntelligence.outputs.docIntelligenceEndPoint
//cognitiveservices.azure.com/
