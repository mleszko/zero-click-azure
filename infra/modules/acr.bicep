@description('Azure region for Azure Container Registry.')
param location string

@description('Globally unique Azure Container Registry name.')
param name string

@description('Azure Container Registry SKU.')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Basic'

@description('Optional resource tags.')
param tags object = {}

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  tags: tags
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    anonymousPullEnabled: false
  }
}

output id string = registry.id
output name string = registry.name
output loginServer string = registry.properties.loginServer
