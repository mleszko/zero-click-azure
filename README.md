# Self-Correcting AI Agent on Azure (100% IaC)

This repository delivers a **zero-click** Azure deployment for a Python FastAPI + LangGraph service, using:

- **Infrastructure as Code**: Bicep (`/infra`)
- **Application**: FastAPI + LangGraph (`/app`)
- **Automation**: GitHub Actions (`.github/workflows/deploy.yml`)
- **Security model**: Managed Identity + least-privilege RBAC (no static cloud credentials in code)

---

## 1) Architecture

The deployment provisions these Azure resources from code:

1. **Azure Container Registry (ACR)** for image storage
2. **User-assigned Managed Identity** for passwordless image pull
3. **Azure Container Apps Environment** (+ Log Analytics workspace)
4. **Azure Container App** hosting FastAPI
5. **RBAC role assignment**: Managed Identity receives `AcrPull` on ACR

The API exposes a LangGraph workflow with a correction loop:

- `generate` -> `grade` -> (`generate` again if failed) -> `finalize`

---

## 2) Repository structure

```text
.
├── infra/
│   ├── main.bicep
│   ├── main.parameters.json
│   └── modules/
│       ├── acr.bicep
│       ├── containerApp.bicep
│       ├── containerAppsEnv.bicep
│       ├── managedIdentity.bicep
│       └── roleAssignments.bicep
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── api/
│   ├── agent/
│   └── core/
└── .github/workflows/deploy.yml
```

---

## 3) Prerequisites (local)

Install and authenticate the following tools:

- Azure CLI (`az`) v2.57+
- GitHub CLI (`gh`)
- Git

Login to Azure:

```bash
az login
az account set --subscription "<SUBSCRIPTION_ID_OR_NAME>"
```

Authenticate GitHub CLI:

```bash
gh auth login
```

---

## 4) One-time setup: OIDC for GitHub Actions (no client secret)

> This creates an Entra app + service principal trusted by GitHub Actions via OIDC.

### 4.1 Define setup variables

```bash
export SUBSCRIPTION_ID="<subscription-id>"
export RESOURCE_GROUP="rg-selfcorragent-dev"
export LOCATION="eastus"
export PROJECT_NAME="selfcorragent"
export REPO_OWNER="<github-org-or-user>"
export REPO_NAME="<github-repo-name>"
export BRANCH_REF="refs/heads/main"
```

### 4.2 Create resource group

```bash
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
```

### 4.3 Create Entra application + service principal

```bash
APP_NAME="gh-${REPO_NAME}-deploy"
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
az ad sp create --id "$APP_ID" >/dev/null
OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)
```

### 4.4 Add federated credential for GitHub branch deployments

```bash
cat > /tmp/gh-oidc-credential.json <<JSON
{
  "name": "github-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:${REPO_OWNER}/${REPO_NAME}:ref:${BRANCH_REF}",
  "description": "OIDC trust for GitHub Actions",
  "audiences": ["api://AzureADTokenExchange"]
}
JSON

az ad app federated-credential create --id "$OBJECT_ID" --parameters /tmp/gh-oidc-credential.json
```

### 4.5 Assign least-privilege deployment role at resource group scope

```bash
az role assignment create \
  --assignee "$APP_ID" \
  --role "Contributor" \
  --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
```

> Why Contributor at RG scope?
> The workflow must create/update Container Apps, ACR, Managed Identity, Log Analytics, and RBAC assignment resources in that RG.

### 4.6 Store GitHub Actions secrets and variables from CLI

```bash
TENANT_ID=$(az account show --query tenantId -o tsv)

printf "%s" "$APP_ID" | gh secret set AZURE_CLIENT_ID --repo "${REPO_OWNER}/${REPO_NAME}"
printf "%s" "$TENANT_ID" | gh secret set AZURE_TENANT_ID --repo "${REPO_OWNER}/${REPO_NAME}"
printf "%s" "$SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID --repo "${REPO_OWNER}/${REPO_NAME}"

gh variable set AZURE_RESOURCE_GROUP --body "$RESOURCE_GROUP" --repo "${REPO_OWNER}/${REPO_NAME}"
gh variable set AZURE_LOCATION --body "$LOCATION" --repo "${REPO_OWNER}/${REPO_NAME}"
gh variable set AZURE_PROJECT_NAME --body "$PROJECT_NAME" --repo "${REPO_OWNER}/${REPO_NAME}"
```

---

## 5) Deploy (GitHub Actions only)

Trigger deployment by pushing code:

```bash
git add .
git commit -m "Deploy self-correcting agent"
git push
```

Or trigger manually:

```bash
gh workflow run deploy.yml --repo "${REPO_OWNER}/${REPO_NAME}"
```

Monitor execution:

```bash
gh run list --workflow deploy.yml --repo "${REPO_OWNER}/${REPO_NAME}"
gh run watch --repo "${REPO_OWNER}/${REPO_NAME}"
```

What the workflow does:

1. Logs in to Azure using OIDC (`azure/login`)
2. Bootstraps Bicep deployment to create ACR/identity/environment
3. Builds + pushes image to ACR using `az acr build`
4. Redeploys Bicep with the released image reference
5. Publishes Container App URL in the workflow summary

---

## 6) Validate deployment with Azure CLI

Get app URL:

```bash
APP_NAME="${PROJECT_NAME}-api"
APP_FQDN=$(az containerapp show -g "$RESOURCE_GROUP" -n "$APP_NAME" --query properties.configuration.ingress.fqdn -o tsv)
echo "https://${APP_FQDN}"
```

Health check:

```bash
curl -s "https://${APP_FQDN}/healthz" | jq
```

Invoke correction loop:

```bash
curl -s -X POST "https://${APP_FQDN}/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize why this architecture is secure.",
    "required_facts": [
      "Managed Identity is used for ACR pull",
      "AcrPull role assignment limits registry access"
    ],
    "max_correction_loops": 3
  }' | jq
```

Inspect logs:

```bash
az containerapp logs show -g "$RESOURCE_GROUP" -n "$APP_NAME" --follow
```

---

## 7) Local development (optional)

```bash
cd app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs:

- `http://localhost:8000/docs`

Run tests:

```bash
pytest
```

---

## 8) Optional Azure OpenAI integration (managed identity)

The service supports an optional Azure OpenAI generation path with graceful fallback to the built-in rule-based generator.

Configure these environment variables in `infra/main.parameters.json` (or override in deployment parameters):

- `ENABLE_AZURE_OPENAI=true`
- `AZURE_OPENAI_ENDPOINT=https://<your-openai-resource>.openai.azure.com`
- `AZURE_OPENAI_DEPLOYMENT=<chat-deployment-name>`
- `AZURE_OPENAI_API_VERSION=2024-06-01`
- `AZURE_OPENAI_MANAGED_IDENTITY_CLIENT_ID=<optional-uami-client-id>`

Recommended RBAC for least privilege:

- Assign your Container App managed identity the `Cognitive Services OpenAI User` role scoped to the Azure OpenAI resource.

---

## 9) Security and least-privilege highlights

- No Azure credentials hardcoded in source.
- GitHub Actions uses OIDC (federated identity), not client secrets.
- Container App pulls image via **user-assigned managed identity**.
- RBAC scope is minimized for image pull (`AcrPull` on ACR).
- Environment configuration is IaC-defined through Bicep parameters.

---

## 10) Cleanup

Delete the resource group:

```bash
az group delete --name "$RESOURCE_GROUP" --yes --no-wait
```

Remove local temp federated credential file:

```bash
rm -f /tmp/gh-oidc-credential.json
```
