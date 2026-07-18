// Infraestrutura como Código (Bicep) — Agente Previdência IA
// Provisiona: Resource Group, Storage Account, Azure AI Search, App Service (rag-api),
// Function App (ingestão assíncrona) e App Registration (Entra ID) com RBAC usuario/admin.

targetScope = 'resourceGroup'

param location string = resourceGroup().location
param appName string = 'agente-previdencia'
param sku string = 'S1' // App Service plan SKU

var ragAppName = '${appName}-rag-api'
var funcAppName = '${appName}-ingest-fn'
var storageName = toLower('${appName}storage')
var searchName = '${appName}-search'
var planName = '${appName}-plan'
var tenantId = tenant().tenantId

// Storage Account (PDFs originais)
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: { accessTier: 'Hot' }
}

// Azure AI Search
resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchName
  location: location
  sku: { name: 'standard' }
  properties: { replicaCount: 1, partitionCount: 1 }
}

// App Service Plan
resource plan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: planName
  location: location
  sku: { name: sku, tier: 'Standard' }
  properties: { reserved: false }
}

// App Service (rag-api)
resource web 'Microsoft.Web/sites@2023-01-01' = {
  name: ragAppName
  location: location
  kind: 'app'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      appSettings: [
        { name: 'VECTOR_STORE', value: 'azure' }
        { name: 'AZURE_AI_SEARCH_ENDPOINT', value: 'https://${searchName}.search.windows.net' }
        { name: 'AZURE_AI_SEARCH_KEY', value: search.listAdminKeys().primaryKey }
        { name: 'LLM_PROVIDER', value: 'azure' }
        { name: 'AZURE_OPENAI_ENDPOINT', value: '' }
        { name: 'AZURE_OPENAI_API_KEY', value: '' }
        { name: 'ENTRA_TENANT_ID', value: tenantId }
        { name: 'ENTRA_CLIENT_ID', value: '' }
      ]
    }
  }
}

// Storage Account para a Function
resource funcPlanStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${storageName}fn'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

// Function App (ingestão assíncrona de documentos)
resource funcApp 'Microsoft.Web/sites@2023-01-01' = {
  name: funcAppName
  location: location
  kind: 'functionapp'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${funcPlanStorage.name};AccountKey=${funcPlanStorage.listKeys().keys[0].value};EndpointSuffix=core.windows.net' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'WEBSITE_RUN_FROM_PACKAGE', value: '1' }
        { name: 'AZURE_AI_SEARCH_ENDPOINT', value: 'https://${searchName}.search.windows.net' }
        { name: 'AZURE_AI_SEARCH_KEY', value: search.listAdminKeys().primaryKey }
      ]
    }
  }
}

// App Registration (Entra ID) — protege os endpoints com auth
resource appReg 'Microsoft.Graph/applications@v1.0' = {
  displayName: '${appName}-api'
  signInAudience: 'AzureADMyOrg'
  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      { id: guid(), type: 'User', value: 'access_as_user', adminConsentDisplayName: 'Acessar API', userConsentDisplayName: 'Acessar API', adminConsentDescription: 'Acesso à API do agente', userConsentDescription: 'Acesso à API do agente' }
    ]
  }
  appRoles: [
    { id: guid(), allowedMemberTypes: ['User'], description: 'Administrador do sistema', displayName: 'Admin', value: 'admin', isEnabled: true }
    { id: guid(), allowedMemberTypes: ['User'], description: 'Usuário comum', displayName: 'Usuario', value: 'usuario', isEnabled: true }
  ]
}

output ragApiUrl string = 'https://${ragAppName}.azurewebsites.net'
output searchService string = searchName
output appRegistrationId string = appReg.id
