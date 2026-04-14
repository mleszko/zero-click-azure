@description('Azure region for the Container App.')
param location string

@description('Container App name.')
param name string

@description('Managed environment resource ID used by the Container App.')
param managedEnvironmentId string

@description('Container image reference.')
param image string

@description('Target ingress port exposed by the FastAPI server.')
param targetPort int = 8000

@description('Container CPU allocation.')
param containerCpu string = '0.5'

@description('Container memory allocation.')
param containerMemory string = '1Gi'

@description('Minimum replica count.')
param minReplicas int = 0

@description('Maximum replica count.')
param maxReplicas int = 3

@description('User-assigned managed identity resource ID attached to the Container App.')
param userAssignedIdentityResourceId string

@description('Azure Container Registry login server used for image pulls.')
param acrLoginServer string

@description('Environment variables passed to the container. Expected shape: [{ name: string, value: string }].')
param environmentVariables array

@description('Optional resource tags.')
param tags object = {}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        allowInsecure: false
        targetPort: targetPort
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: acrLoginServer
          identity: userAssignedIdentityResourceId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: image
          env: [for envVar in environmentVariables: {
            name: envVar.name
            value: string(envVar.value)
          }]
          resources: {
            cpu: json(containerCpu)
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

output id string = app.id
output name string = app.name
output latestRevisionName string = app.properties.latestRevisionName
output url string = 'https://${app.properties.configuration.ingress.fqdn}'
