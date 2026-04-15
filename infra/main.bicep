targetScope = 'resourceGroup'

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short project identifier used in resource names.')
@maxLength(20)
param projectName string = 'selfcorragent'

@description('Container image reference in the target ACR (for example: myacr.azurecr.io/self-correcting-agent:sha).')
param containerImage string

@description('Container CPU allocation for the FastAPI container.')
param containerCpu string = '0.5'

@description('Container memory allocation for the FastAPI container.')
param containerMemory string = '1Gi'

@description('Port exposed by the FastAPI app.')
@minValue(1)
@maxValue(65535)
param targetPort int = 8000

@description('Minimum number of running replicas in Azure Container Apps.')
@minValue(0)
param minReplicas int = 0

@description('Maximum number of running replicas in Azure Container Apps.')
@minValue(1)
param maxReplicas int = 3

@description('Container Registry SKU.')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param acrSku string = 'Basic'

@description('Application environment variables injected into the container.')
param environmentVariables array = [
  {
    name: 'APP_ENV'
    value: 'production'
  }
  {
    name: 'LOG_LEVEL'
    value: 'INFO'
  }
  {
    name: 'MAX_CORRECTION_LOOPS'
    value: '3'
  }
  {
    name: 'DEFAULT_MODEL_NAME'
    value: 'rule-based-correction-graph'
  }
  {
    name: 'ENABLE_AZURE_OPENAI'
    value: 'false'
  }
  {
    name: 'AZURE_OPENAI_API_VERSION'
    value: '2024-06-01'
  }
  {
    name: 'AZURE_OPENAI_ENDPOINT'
    value: ''
  }
  {
    name: 'AZURE_OPENAI_DEPLOYMENT'
    value: ''
  }
  {
    name: 'AZURE_OPENAI_MANAGED_IDENTITY_CLIENT_ID'
    value: ''
  }
]

@description('Optional resource tags.')
param tags object = {}

var normalizedProjectName = toLower(replace(replace(projectName, '-', ''), '_', ''))
var suffix = uniqueString(resourceGroup().id, projectName)
var acrName = take('${normalizedProjectName}${suffix}', 50)
var identityName = '${projectName}-uami'
var containerAppsEnvName = '${projectName}-cae'
var logAnalyticsWorkspaceName = '${projectName}-law'
var containerAppName = '${projectName}-api'

module acr './modules/acr.bicep' = {
  name: 'acr-deployment'
  params: {
    location: location
    name: acrName
    sku: acrSku
    tags: tags
  }
}

module managedIdentity './modules/managedIdentity.bicep' = {
  name: 'managed-identity-deployment'
  params: {
    location: location
    name: identityName
    tags: tags
  }
}

module containerAppsEnv './modules/containerAppsEnv.bicep' = {
  name: 'container-apps-environment-deployment'
  params: {
    location: location
    name: containerAppsEnvName
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
    tags: tags
  }
}

module acrPullRole './modules/roleAssignments.bicep' = {
  name: 'acr-pull-role-assignment'
  params: {
    acrName: acr.outputs.name
    principalId: managedIdentity.outputs.principalId
  }
}

module containerApp './modules/containerApp.bicep' = {
  name: 'container-app-deployment'
  params: {
    acrLoginServer: acr.outputs.loginServer
    containerCpu: containerCpu
    containerMemory: containerMemory
    environmentVariables: environmentVariables
    image: containerImage
    location: location
    managedEnvironmentId: containerAppsEnv.outputs.id
    maxReplicas: maxReplicas
    minReplicas: minReplicas
    name: containerAppName
    targetPort: targetPort
    userAssignedIdentityResourceId: managedIdentity.outputs.id
    tags: tags
  }
  dependsOn: [
    acrPullRole
  ]
}

output acrId string = acr.outputs.id
output acrName string = acr.outputs.name
output acrLoginServer string = acr.outputs.loginServer
output managedIdentityId string = managedIdentity.outputs.id
output managedIdentityPrincipalId string = managedIdentity.outputs.principalId
output containerAppsEnvironmentId string = containerAppsEnv.outputs.id
output containerAppName string = containerApp.outputs.name
output containerAppUrl string = containerApp.outputs.url
