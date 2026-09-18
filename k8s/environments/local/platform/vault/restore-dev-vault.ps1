[CmdletBinding()]
param(
    [string]$VaultNamespace = "vault",
    [string]$VaultToken = "root",
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)

function Invoke-Kubectl {
    param([Parameter(Mandatory)][string[]]$CommandArgs)

    & kubectl @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "kubectl failed: kubectl $($CommandArgs -join ' ')"
    }
}

function Get-KubernetesSecretData {
    param(
        [Parameter(Mandatory)][string]$Namespace,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string[]]$RequiredKeys
    )

    $raw = & kubectl get secret $Name -n $Namespace -o json 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to read recovery source Secret $Namespace/$Name`: $($raw -join ' ')"
    }

    $secret = ($raw -join "`n") | ConvertFrom-Json
    $decoded = @{}
    foreach ($property in $secret.data.PSObject.Properties) {
        $decoded[$property.Name] = [Text.Encoding]::UTF8.GetString(
            [Convert]::FromBase64String([string]$property.Value)
        )
    }

    foreach ($key in $RequiredKeys) {
        if (-not $decoded.ContainsKey($key) -or [string]::IsNullOrEmpty($decoded[$key])) {
            throw "Recovery source Secret $Namespace/$Name is missing required key '$key'."
        }
    }

    return ,$decoded
}

function Wait-ExternalSecretRefresh {
    param(
        [Parameter(Mandatory)][string]$Namespace,
        [Parameter(Mandatory)][hashtable]$PreviousRefreshTimes
    )

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $raw = & kubectl get externalsecret -n $Namespace -o json 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to inspect ExternalSecrets in namespace $Namespace`: $($raw -join ' ')"
        }

        $resources = (($raw -join "`n") | ConvertFrom-Json).items
        $pending = @($resources | Where-Object {
            $ready = @($_.status.conditions | Where-Object {
                $_.type -eq "Ready" -and $_.status -eq "True"
            }).Count -gt 0
            $previous = $PreviousRefreshTimes[$_.metadata.name]
            $refreshed = $_.status.refreshTime -and (
                [DateTimeOffset]::Parse($_.status.refreshTime) -gt $previous
            )
            -not ($ready -and $refreshed)
        })

        if ($pending.Count -eq 0) {
            Write-Host "ExternalSecrets refreshed in namespace $Namespace"
            return
        }

        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)

    throw "Timed out waiting for a fresh ExternalSecret sync in namespace $Namespace`: $($pending.metadata.name -join ', ')"
}

function Get-ExternalSecretRefreshTimes {
    param([Parameter(Mandatory)][string]$Namespace)

    $raw = & kubectl get externalsecret -n $Namespace -o json 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to inspect ExternalSecrets in namespace $Namespace`: $($raw -join ' ')"
    }

    $refreshTimes = @{}
    foreach ($resource in (($raw -join "`n") | ConvertFrom-Json).items) {
        $refreshTimes[$resource.metadata.name] = if ($resource.status.refreshTime) {
            [DateTimeOffset]::Parse($resource.status.refreshTime)
        } else {
            [DateTimeOffset]::MinValue
        }
    }
    return ,$refreshTimes
}

function Write-VaultSecret {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][hashtable]$Data
    )

    $json = ConvertTo-Json -InputObject $Data -Compress
    $result = $json | & kubectl exec -i -n $VaultNamespace $script:VaultPod -- `
        env "VAULT_ADDR=http://127.0.0.1:8200" "VAULT_TOKEN=$VaultToken" `
        vault kv put "secret/$Path" -
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to restore Vault path secret/$Path."
    }

    Write-Host "Restored secret/$Path"
}

if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    throw "kubectl is not available in PATH."
}

$policyFile = Join-Path $PSScriptRoot "task-api-read-policy.hcl"
if (-not (Test-Path -LiteralPath $policyFile)) {
    throw "Vault policy file not found: $policyFile"
}

Write-Host "Waiting for local Vault..."
Invoke-Kubectl @(
    "rollout", "status", "deployment/vault",
    "-n", $VaultNamespace,
    "--timeout=$($TimeoutSeconds)s"
)

$vaultPodsRaw = & kubectl get pod -n $VaultNamespace -l app=vault -o json 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Failed to inspect Vault pods: $($vaultPodsRaw -join ' ')"
}
$script:VaultPod = ((($vaultPodsRaw -join "`n") | ConvertFrom-Json).items | Where-Object {
    $_.status.phase -eq "Running" -and
    -not $_.metadata.PSObject.Properties["deletionTimestamp"] -and
    @($_.status.conditions | Where-Object {
        $_.type -eq "Ready" -and $_.status -eq "True"
    }).Count -gt 0
} | Sort-Object { [DateTimeOffset]::Parse($_.metadata.creationTimestamp) } -Descending |
    Select-Object -First 1).metadata.name
if ([string]::IsNullOrWhiteSpace($script:VaultPod)) {
    throw "Could not find the Vault pod in namespace $VaultNamespace."
}

$policyContent = Get-Content -LiteralPath $policyFile -Raw
$policyCopy = $policyContent | & kubectl exec -i -n $VaultNamespace $script:VaultPod -- `
    tee /tmp/task-api-read.hcl
if ($LASTEXITCODE -ne 0) {
    throw "Failed to copy the Vault policy into pod $script:VaultPod."
}

$vaultEnvironment = @(
    "env",
    "VAULT_ADDR=http://127.0.0.1:8200",
    "VAULT_TOKEN=$VaultToken"
)
$authList = & kubectl exec -n $VaultNamespace $script:VaultPod -- `
    @vaultEnvironment vault auth list -format=json
if ($LASTEXITCODE -ne 0) {
    throw "Failed to inspect Vault auth methods."
}
if (($authList -join "`n") -notmatch '"kubernetes/"') {
    Invoke-Kubectl @(
        "exec", "-n", $VaultNamespace, $script:VaultPod, "--",
        $vaultEnvironment[0], $vaultEnvironment[1], $vaultEnvironment[2],
        "vault", "auth", "enable", "kubernetes"
    )
}

Invoke-Kubectl @(
    "exec", "-n", $VaultNamespace, $script:VaultPod, "--",
    $vaultEnvironment[0], $vaultEnvironment[1], $vaultEnvironment[2],
    "vault", "write", "auth/kubernetes/config",
    "kubernetes_host=https://kubernetes.default.svc:443",
    "kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
    "token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token"
)
Invoke-Kubectl @(
    "exec", "-n", $VaultNamespace, $script:VaultPod, "--",
    $vaultEnvironment[0], $vaultEnvironment[1], $vaultEnvironment[2],
    "vault", "policy", "write", "task-api-read", "/tmp/task-api-read.hcl"
)
Invoke-Kubectl @(
    "exec", "-n", $VaultNamespace, $script:VaultPod, "--",
    $vaultEnvironment[0], $vaultEnvironment[1], $vaultEnvironment[2],
    "vault", "write", "auth/kubernetes/role/task-api",
    "bound_service_account_names=vault-secret-reader",
    "bound_service_account_namespaces=task-api",
    "policies=task-api-read",
    "ttl=1h"
)
Write-Host "Restored Vault Kubernetes auth, policy, and role"

$shared = Get-KubernetesSecretData -Namespace "task-api" -Name "postgres-credentials" `
    -RequiredKeys @("POSTGRES_USER", "POSTGRES_PASSWORD", "REDIS_PASSWORD")
$redis = Get-KubernetesSecretData -Namespace "task-api" -Name "redis-cluster-auth" `
    -RequiredKeys @("password", "REDIS_PASSWORD")
$shared["REDIS_PASSWORD"] = $redis["password"]

Write-VaultSecret -Path "platform/shared" -Data $shared
Write-VaultSecret -Path "task-service/db" -Data (
    Get-KubernetesSecretData -Namespace "task-api" -Name "task-service-db-from-vault" `
        -RequiredKeys @("username", "password")
)
Write-VaultSecret -Path "task-db/backup" -Data (
    Get-KubernetesSecretData -Namespace "task-api" -Name "task-db-backup-s3" `
        -RequiredKeys @("ACCESS_KEY_ID", "ACCESS_SECRET_KEY")
)
Write-VaultSecret -Path "pgadmin/config" -Data (
    Get-KubernetesSecretData -Namespace "task-api" -Name "pgadmin" `
        -RequiredKeys @("PGADMIN_DEFAULT_EMAIL", "PGADMIN_DEFAULT_PASSWORD")
)
Write-VaultSecret -Path "kibana/encryption-keys" -Data (
    Get-KubernetesSecretData -Namespace "task-api" -Name "kibana-encryption-keys" `
        -RequiredKeys @("securityEncryptionKey", "savedObjectsEncryptionKey", "reportingEncryptionKey")
)
Write-VaultSecret -Path "task-api/config" -Data (
    Get-KubernetesSecretData -Namespace "task-api" -Name "task-api-config" `
        -RequiredKeys @("username", "password")
)

$previousRefreshTimes = @{}
foreach ($namespace in @("task-api", "monitoring")) {
    $previousRefreshTimes[$namespace] = Get-ExternalSecretRefreshTimes -Namespace $namespace
}

$syncTimestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
foreach ($namespace in @("task-api", "monitoring")) {
    Invoke-Kubectl @(
        "annotate", "externalsecret", "--all", "-n", $namespace,
        "force-sync=$syncTimestamp", "--overwrite"
    )
}

Invoke-Kubectl @(
    "wait", "secretstore/vault-task-api", "-n", "task-api",
    "--for=condition=Ready", "--timeout=$($TimeoutSeconds)s"
)
Invoke-Kubectl @(
    "wait", "clustersecretstore/vault-platform",
    "--for=condition=Ready", "--timeout=$($TimeoutSeconds)s"
)
foreach ($namespace in @("task-api", "monitoring")) {
    Wait-ExternalSecretRefresh -Namespace $namespace `
        -PreviousRefreshTimes $previousRefreshTimes[$namespace]
}

Write-Host "Vault recovery completed. External Secrets status:"
Invoke-Kubectl @("get", "externalsecret", "-A")
