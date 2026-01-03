# ============================================================================
# MLOps Workshop - Status Check
# ============================================================================
# This script shows the status of all deployed components
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLOps Workshop - Status" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check cluster
Write-Host "Cluster:" -ForegroundColor Yellow
$clusters = kind get clusters 2>$null
if ($clusters -contains $ClusterName) {
    Write-Host "  ✓ Cluster '$ClusterName' is running" -ForegroundColor Green
} else {
    Write-Host "  ✗ Cluster '$ClusterName' not found" -ForegroundColor Red
    Write-Host "  Run: .\scripts\deploy-all.ps1" -ForegroundColor Yellow
    exit 1
}

# Set context
kubectl config use-context kind-$ClusterName 2>$null | Out-Null

Write-Host ""
Write-Host "Nodes:" -ForegroundColor Yellow
kubectl get nodes -o wide

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " PostgreSQL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
kubectl get pods,svc -n postgres

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MinIO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
kubectl get pods,svc -n minio

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLflow" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
kubectl get pods,svc -n mlflow

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Airflow" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
kubectl get pods,svc -n airflow

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Access URLs" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Airflow UI:    http://localhost:8080  (admin/admin123)" -ForegroundColor Cyan
Write-Host "MLflow UI:     http://localhost:5000" -ForegroundColor Cyan
Write-Host "MinIO Console: http://localhost:9001  (minioadmin/minioadmin123)" -ForegroundColor Cyan

