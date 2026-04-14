@description('Azure region for the Container Apps environment.')
param location string

@description('Container Apps environment name.')
param name string

@description('Log Analytics workspace name.')
param logAnalyticsWorkspaceName string

@description('Optional resource tags.')
param tags object = {}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: tags
  sku: {
    name: 'PerGB2018'
  }
  properties: {
    retentionInDays: 30
  }
}

var logAnalyticsSharedKey = listKeys(logAnalyticsWorkspace.id, '2022-10-01').primarySharedKey

resource managedEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    zoneRedundant: false
  }
}

output id string = managedEnvironment.id
output name string = managedEnvironment.name
output defaultDomain string = managedEnvironment.properties.defaultDomain
output staticIp string = managedEnvironment.properties.staticIp
