# ============================================================================
# MLOps Workshop - Enable Git-Sync for Airflow DAGs
# ============================================================================
# This script enables Git-sync to fetch DAGs from a GitHub repository
# ============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$GitRepoUrl,
    [string]$Branch = "main",
    [string]$DagsFolder = "dags",
    [string]$ClusterName = "mlops-workshop"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLOps Workshop - Enable Git-Sync" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Git Repository: $GitRepoUrl" -ForegroundColor Yellow
Write-Host "Branch: $Branch" -ForegroundColor Yellow
Write-Host "DAGs Folder: $DagsFolder" -ForegroundColor Yellow
Write-Host ""

# Verify cluster context
kubectl config use-context kind-$ClusterName 2>$null

$k8sPath = Join-Path $PSScriptRoot "..\k8s"

# Update Git-sync configmap
Write-Host "[1/4] Updating Git-sync configuration..." -ForegroundColor Yellow

$configMap = @"
# Git-Sync Configuration for Airflow DAGs
apiVersion: v1
kind: ConfigMap
metadata:
  name: git-sync-config
  namespace: airflow
  labels:
    app.kubernetes.io/name: airflow
    app.kubernetes.io/part-of: mlops-workshop
data:
  GIT_SYNC_REPO: "$GitRepoUrl"
  GIT_SYNC_BRANCH: "$Branch"
  GIT_SYNC_DEPTH: "1"
  GIT_SYNC_ROOT: "/git"
  GIT_SYNC_DEST: "repo"
  GIT_SYNC_WAIT: "60"
  GIT_SYNC_MAX_FAILURES: "5"
"@

$configMap | Set-Content (Join-Path $k8sPath "airflow\airflow-git-sync-configmap.yaml")
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-git-sync-configmap.yaml")
Write-Host "  ✓ Git-sync configmap updated" -ForegroundColor Green

# Update scheduler and webserver to use Git-sync
Write-Host "[2/4] Updating Airflow deployments..." -ForegroundColor Yellow

# Update the DAGs folder path in the deployments
$schedulerPath = Join-Path $k8sPath "airflow\airflow-scheduler.yaml"
$webserverPath = Join-Path $k8sPath "airflow\airflow-webserver.yaml"

$dagsPath = "/git/repo/$DagsFolder"

$schedulerContent = Get-Content $schedulerPath -Raw
$schedulerContent = $schedulerContent -replace 'value: "/git/repo/airflow/example_dags"', "value: `"$dagsPath`""
$schedulerContent | Set-Content $schedulerPath

$webserverContent = Get-Content $webserverPath -Raw
$webserverContent = $webserverContent -replace 'value: "/git/repo/airflow/example_dags"', "value: `"$dagsPath`""
$webserverContent | Set-Content $webserverPath

Write-Host "  ✓ Deployments updated with DAGs path: $dagsPath" -ForegroundColor Green

# Delete current deployments
Write-Host "[3/4] Recreating Airflow deployments with Git-sync..." -ForegroundColor Yellow
kubectl delete deployment airflow-scheduler -n airflow --ignore-not-found
kubectl delete deployment airflow-webserver -n airflow --ignore-not-found

Start-Sleep -Seconds 5

kubectl apply -f $schedulerPath
kubectl apply -f $webserverPath
Write-Host "  ✓ Deployments recreated" -ForegroundColor Green

# Wait for pods
Write-Host "[4/4] Waiting for Airflow to be ready..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes (cloning repo)..." -ForegroundColor Gray
kubectl wait --namespace airflow --for=condition=ready pod -l app=airflow-webserver --timeout=300s
kubectl wait --namespace airflow --for=condition=ready pod -l app=airflow-scheduler --timeout=300s
Write-Host "  ✓ Airflow is ready with Git-sync" -ForegroundColor Green

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Git-Sync Enabled!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your DAGs will be synced from:" -ForegroundColor Yellow
Write-Host "  Repository: $GitRepoUrl" -ForegroundColor Cyan
Write-Host "  Branch: $Branch" -ForegroundColor Cyan
Write-Host "  DAGs Path: $DagsFolder" -ForegroundColor Cyan
Write-Host ""
Write-Host "DAGs will automatically sync every 60 seconds." -ForegroundColor Gray
Write-Host ""
Write-Host "To check sync status:" -ForegroundColor Yellow
Write-Host "  kubectl logs deployment/airflow-scheduler -n airflow -c git-sync" -ForegroundColor Gray

