@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Name prefix for Container Apps environment and apps.')
param namePrefix string = 'hloadai'

@description('Container image for the API (e.g. myregistry.azurecr.io/high-load-ai:latest).')
param apiImage string

@description('Container image for the Celery worker (often same as API image).')
param workerImage string

@description('PostgreSQL connection string for the API (store secret in Key Vault in production).')
@secure()
param databaseUrl string

@description('Redis URL for rate limiting and Celery (store secret in Key Vault in production).')
@secure()
param redisUrl string

@description('Celery broker URL.')
@secure()
param celeryBrokerUrl string

@description('Celery result backend URL.')
@secure()
param celeryResultBackend string

@description('Comma-separated API keys for X-API-Key auth.')
@secure()
param apiKeys string

@description('LLM base URL (OpenAI-compatible).')
param llmBaseUrl string = 'https://api.openai.com/v1'

@description('LLM API key.')
@secure()
param llmApiKey string

@description('LLM model name.')
param llmModel string = 'gpt-4o-mini'

@description('Self-hosted Langfuse base URL (optional).')
param langfuseHost string = ''

@description('Langfuse public key (optional).')
@secure()
param langfusePublicKey string = ''

@description('Langfuse secret key (optional).')
@secure()
param langfuseSecretKey string = ''

var logAnalyticsName = '${namePrefix}-logs'
var containerAppsEnvName = '${namePrefix}-cae'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-api'
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        { name: 'database-url'; value: databaseUrl }
        { name: 'redis-url'; value: redisUrl }
        { name: 'celery-broker-url'; value: celeryBrokerUrl }
        { name: 'celery-result-backend'; value: celeryResultBackend }
        { name: 'api-keys'; value: apiKeys }
        { name: 'llm-api-key'; value: llmApiKey }
        { name: 'langfuse-public-key'; value: langfusePublicKey }
        { name: 'langfuse-secret-key'; value: langfuseSecretKey }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'DATABASE_URL'; secretRef: 'database-url' }
            { name: 'REDIS_URL'; secretRef: 'redis-url' }
            { name: 'CELERY_BROKER_URL'; secretRef: 'celery-broker-url' }
            { name: 'CELERY_RESULT_BACKEND'; secretRef: 'celery-result-backend' }
            { name: 'API_KEYS'; secretRef: 'api-keys' }
            { name: 'LLM_BASE_URL'; value: llmBaseUrl }
            { name: 'LLM_API_KEY'; secretRef: 'llm-api-key' }
            { name: 'LLM_MODEL'; value: llmModel }
            { name: 'LANGFUSE_HOST'; value: langfuseHost }
            { name: 'LANGFUSE_PUBLIC_KEY'; secretRef: 'langfuse-public-key' }
            { name: 'LANGFUSE_SECRET_KEY'; secretRef: 'langfuse-secret-key' }
            { name: 'TRACING_ENABLED'; value: 'true' }
          ]
        }
      ]
    }
  }
}

resource workerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-worker'
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: false
      }
      secrets: [
        { name: 'database-url'; value: databaseUrl }
        { name: 'redis-url'; value: redisUrl }
        { name: 'celery-broker-url'; value: celeryBrokerUrl }
        { name: 'celery-result-backend'; value: celeryResultBackend }
      ]
    }
    template: {
      scale: {
        minReplicas: 1
        maxReplicas: 5
      }
      containers: [
        {
          name: 'worker'
          image: workerImage
          command: ['celery', '-A', 'high_load_ai.infrastructure.tasks.celery_app', 'worker', '--loglevel=INFO']
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'DATABASE_URL'; secretRef: 'database-url' }
            { name: 'REDIS_URL'; secretRef: 'redis-url' }
            { name: 'CELERY_BROKER_URL'; secretRef: 'celery-broker-url' }
            { name: 'CELERY_RESULT_BACKEND'; secretRef: 'celery-result-backend' }
          ]
        }
      ]
    }
  }
}

output apiFqdn string = apiApp.properties.configuration.ingress.fqdn
