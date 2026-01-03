# ============================================================================
# MLOps Workshop - Step 3: Deploy MLflow
# ============================================================================
# This script deploys MLflow Tracking Server with PostgreSQL and MinIO
# Prerequisites: Infrastructure deployed (run 02-deploy-infrastructure.ps1 first)
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLOps Workshop - Deploy MLflow" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verify cluster context
Write-Host "[1/4] Verifying cluster context..." -ForegroundColor Yellow
kubectl config use-context kind-$ClusterName 2>$null
Write-Host "  ✓ Using context: kind-$ClusterName" -ForegroundColor Green

# Verify prerequisites
Write-Host "[2/4] Verifying prerequisites..." -ForegroundColor Yellow
$pgReady = kubectl get pods -n postgres -l app=postgres -o jsonpath='{.items[0].status.phase}' 2>$null
$minioReady = kubectl get pods -n minio -l app=minio -o jsonpath='{.items[0].status.phase}' 2>$null

if ($pgReady -ne "Running") {
    Write-Host "  ✗ PostgreSQL is not running. Please run 02-deploy-infrastructure.ps1 first." -ForegroundColor Red
    exit 1
}
if ($minioReady -ne "Running") {
    Write-Host "  ✗ MinIO is not running. Please run 02-deploy-infrastructure.ps1 first." -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ PostgreSQL is running" -ForegroundColor Green
Write-Host "  ✓ MinIO is running" -ForegroundColor Green

# Get script directory for relative paths
$k8sPath = Join-Path $PSScriptRoot "..\k8s"

# Deploy MLflow
Write-Host "[3/4] Deploying MLflow..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "mlflow\mlflow-secrets.yaml")
kubectl apply -f (Join-Path $k8sPath "mlflow\mlflow-deployment.yaml")
kubectl apply -f (Join-Path $k8sPath "mlflow\mlflow-service.yaml")
Write-Host "  ✓ MLflow deployed" -ForegroundColor Green

# Wait for MLflow
Write-Host "[4/4] Waiting for MLflow to be ready..." -ForegroundColor Yellow
kubectl wait --namespace mlflow --for=condition=ready pod -l app=mlflow --timeout=180s
Write-Host "  ✓ MLflow is ready" -ForegroundColor Green

# Status
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLflow Status" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
kubectl get pods -n mlflow
Write-Host ""
kubectl get svc -n mlflow

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " MLflow Deployed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "MLflow UI: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "MLflow is configured with:" -ForegroundColor Yellow
Write-Host "  - Backend Store: PostgreSQL (mlflow database)" -ForegroundColor Gray
Write-Host "  - Artifact Store: MinIO (s3://mlflow-artifacts)" -ForegroundColor Gray
Write-Host ""
Write-Host "Next step: Run 04-deploy-airflow.ps1" -ForegroundColor Cyan

