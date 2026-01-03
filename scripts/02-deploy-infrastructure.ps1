# ============================================================================
# MLOps Workshop - Step 2: Deploy Infrastructure
# ============================================================================
# This script deploys PostgreSQL and MinIO to the Kind cluster
# Prerequisites: Kind cluster running (run 01-create-cluster.ps1 first)
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLOps Workshop - Deploy Infrastructure" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verify cluster context
Write-Host "[1/6] Verifying cluster context..." -ForegroundColor Yellow
$currentContext = kubectl config current-context
if ($currentContext -ne "kind-$ClusterName") {
    Write-Host "  Switching to kind-$ClusterName context..." -ForegroundColor Yellow
    kubectl config use-context kind-$ClusterName
}
Write-Host "  ✓ Using context: kind-$ClusterName" -ForegroundColor Green

# Get script directory for relative paths
$k8sPath = Join-Path $PSScriptRoot "..\k8s"

# Create namespaces
Write-Host "[2/6] Creating namespaces..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "namespaces\namespaces.yaml")
Write-Host "  ✓ Namespaces created" -ForegroundColor Green

# Deploy PostgreSQL
Write-Host "[3/6] Deploying PostgreSQL..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "postgres\postgres-secrets.yaml")
kubectl apply -f (Join-Path $k8sPath "postgres\postgres-configmap.yaml")
kubectl apply -f (Join-Path $k8sPath "postgres\postgres-pvc.yaml")
kubectl apply -f (Join-Path $k8sPath "postgres\postgres-deployment.yaml")
kubectl apply -f (Join-Path $k8sPath "postgres\postgres-service.yaml")
Write-Host "  ✓ PostgreSQL deployed" -ForegroundColor Green

# Wait for PostgreSQL
Write-Host "[4/6] Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
kubectl wait --namespace postgres --for=condition=ready pod -l app=postgres --timeout=120s
Write-Host "  ✓ PostgreSQL is ready" -ForegroundColor Green

# Deploy MinIO
Write-Host "[5/6] Deploying MinIO..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "minio\minio-secrets.yaml")
kubectl apply -f (Join-Path $k8sPath "minio\minio-pvc.yaml")
kubectl apply -f (Join-Path $k8sPath "minio\minio-deployment.yaml")
kubectl apply -f (Join-Path $k8sPath "minio\minio-service.yaml")
Write-Host "  ✓ MinIO deployed" -ForegroundColor Green

# Wait for MinIO
Write-Host "[6/6] Waiting for MinIO to be ready..." -ForegroundColor Yellow
kubectl wait --namespace minio --for=condition=ready pod -l app=minio --timeout=120s
Write-Host "  ✓ MinIO is ready" -ForegroundColor Green

# Create MinIO buckets
Write-Host ""
Write-Host "Creating MinIO buckets..." -ForegroundColor Yellow
kubectl apply -f (Join-Path $k8sPath "minio\minio-bucket-job.yaml")
Write-Host "  ✓ Bucket creation job started" -ForegroundColor Green

# Status
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Infrastructure Status" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PostgreSQL:" -ForegroundColor Yellow
kubectl get pods -n postgres
Write-Host ""
Write-Host "MinIO:" -ForegroundColor Yellow
kubectl get pods -n minio

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Infrastructure Deployed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "MinIO Console: http://localhost:9001" -ForegroundColor Cyan
Write-Host "  Username: minioadmin" -ForegroundColor Gray
Write-Host "  Password: minioadmin123" -ForegroundColor Gray
Write-Host ""
Write-Host "Next step: Run 03-deploy-mlflow.ps1" -ForegroundColor Cyan

