# Azure deployment (Container Apps)

This folder contains Bicep templates for deploying the API and worker to Azure Container Apps.

## Prerequisites

- Azure CLI installed and logged in.
- Existing resource group.
- Container image(s) already pushed to ACR or another registry accessible by Container Apps.

## Deploy

```bash
az deployment group create \
  --resource-group <rg-name> \
  --template-file /workspace/deploy/main.bicep \
  --parameters \
    namePrefix=hloadai \
    apiImage=<registry>/high-load-ai:latest \
    workerImage=<registry>/high-load-ai:latest \
    databaseUrl='postgresql+asyncpg://...' \
    redisUrl='redis://...' \
    celeryBrokerUrl='redis://.../1' \
    celeryResultBackend='redis://.../2' \
    apiKeys='prod-key-1,prod-key-2' \
    llmApiKey='<secret>'
```

For production, migrate secret values to Key Vault references in Bicep and remove raw secret parameter usage.
