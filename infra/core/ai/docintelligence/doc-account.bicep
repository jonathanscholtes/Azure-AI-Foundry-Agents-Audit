param accountName string
param identityName string

@description('Azure region where all resources will be deployed (e.g., "eastus")')
param location string


resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing= {
  name: identityName
}


resource doc_account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'FormRecognizer'
  identity: {
    type: 'None'
  }
  properties: {
    customSubDomainName: accountName
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
    allowProjectManagement: false
    publicNetworkAccess: 'Enabled'
  }
}


resource roleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(managedIdentity.id, doc_account.id, 'cognitive-services-openai-contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908') // Cognitive Services User role ID
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
  scope:doc_account
}



output docIntelligenceAccountName string = accountName
output docIntelligenceEndPoint string = doc_account.properties.endpoint
