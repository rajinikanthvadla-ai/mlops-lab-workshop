# ============================================================================
# MLOps Workshop - Step 4: Deploy Airflow
# ============================================================================
# This script deploys Apache Airflow with example DAGs
# Prerequisites: MLflow deployed (run 03-deploy-mlflow.ps1 first)
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop",
    [switch]$UseGitSync,
    [string]$GitRepoUrl = ""
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLOps Workshop - Deploy Airflow" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verify cluster context
Write-Host "[1/6] Verifying cluster context..." -ForegroundColor Yellow
kubectl config use-context kind-$ClusterName 2>$null
Write-Host "  ✓ Using context: kind-$ClusterName" -ForegroundColor Green

# Get script directory for relative paths
$k8sPath = Join-Path $PSScriptRoot "..\k8s"

# Deploy Airflow configs and secrets
Write-Host "[2/6] Deploying Airflow configuration..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-secrets.yaml")
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-configmap.yaml")
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-pvc.yaml")
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-dags-configmap.yaml")

if ($UseGitSync) {
    Write-Host "  Configuring Git-sync..." -ForegroundColor Gray
    if ($GitRepoUrl -ne "") {
        $configMapPath = Join-Path $k8sPath "airflow\airflow-git-sync-configmap.yaml"
        $content = Get-Content $configMapPath -Raw
        $content = $content -replace 'GIT_SYNC_REPO: "https://github.com/apache/airflow.git"', "GIT_SYNC_REPO: `"$GitRepoUrl`""
        $content | Set-Content $configMapPath
        Write-Host "  Git repo: $GitRepoUrl" -ForegroundColor Gray
    }
    kubectl apply -f (Join-Path $k8sPath "airflow\airflow-git-sync-configmap.yaml")
}
Write-Host "  ✓ Airflow configuration deployed" -ForegroundColor Green

# Initialize Airflow database
Write-Host "[3/6] Initializing Airflow database..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-init-job.yaml")

# Wait for init job to complete
Write-Host "  Waiting for database initialization..." -ForegroundColor Gray
kubectl wait --namespace airflow --for=condition=complete job/airflow-init-db --timeout=180s
Write-Host "  ✓ Airflow database initialized" -ForegroundColor Green

# Deploy Airflow components
Write-Host "[4/6] Deploying Airflow components..." -ForegroundColor Yellow
if ($UseGitSync) {
    Write-Host "  Using Git-sync mode" -ForegroundColor Gray
    kubectl apply -f (Join-Path $k8sPath "airflow\airflow-scheduler.yaml")
    kubectl apply -f (Join-Path $k8sPath "airflow\airflow-webserver.yaml")
} else {
    Write-Host "  Using simple mode (ConfigMap DAGs)" -ForegroundColor Gray
    kubectl apply -f (Join-Path $k8sPath "airflow\airflow-scheduler-simple.yaml")
    kubectl apply -f (Join-Path $k8sPath "airflow\airflow-webserver-simple.yaml")
}
kubectl apply -f (Join-Path $k8sPath "airflow\airflow-service.yaml")
Write-Host "  ✓ Airflow components deployed" -ForegroundColor Green

# Wait for Airflow
Write-Host "[5/6] Waiting for Airflow to be ready..." -ForegroundColor Yellow
Write-Host "  This may take 1-2 minutes..." -ForegroundColor Gray
kubectl wait --namespace airflow --for=condition=ready pod -l app=airflow-webserver --timeout=300s
kubectl wait --namespace airflow --for=condition=ready pod -l app=airflow-scheduler --timeout=300s
Write-Host "  ✓ Airflow is ready" -ForegroundColor Green

# Status
Write-Host "[6/6] Checking status..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Airflow Status" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
kubectl get pods -n airflow
Write-Host ""
kubectl get svc -n airflow

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Airflow Deployed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Airflow UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor Gray
Write-Host "  Password: admin123" -ForegroundColor Gray
Write-Host ""
Write-Host "Airflow is configured with:" -ForegroundColor Yellow
Write-Host "  - Database: PostgreSQL" -ForegroundColor Gray
Write-Host "  - Executor: LocalExecutor" -ForegroundColor Gray
if ($UseGitSync) {
    Write-Host "  - DAGs: Git-sync from GitHub" -ForegroundColor Gray
} else {
    Write-Host "  - DAGs: ConfigMap (example_hello_world, example_mlflow_integration)" -ForegroundColor Gray
}
Write-Host "  - MLflow: Connected to http://mlflow.mlflow.svc.cluster.local:5000" -ForegroundColor Gray
Write-Host "  - MinIO: Connected to http://minio.minio.svc.cluster.local:9000" -ForegroundColor Gray
Write-Host ""
if (-not $UseGitSync) {
    Write-Host "To enable Git-sync for DAGs from GitHub, run:" -ForegroundColor Yellow
    Write-Host '  .\scripts\enable-git-sync.ps1 -GitRepoUrl "https://github.com/your-org/your-dags.git"' -ForegroundColor Gray
}
