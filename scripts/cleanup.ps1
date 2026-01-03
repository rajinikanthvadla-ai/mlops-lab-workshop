# ============================================================================
# MLOps Workshop - Cleanup
# ============================================================================
# This script deletes the Kind cluster and all resources
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop"
)

Write-Host "============================================" -ForegroundColor Red
Write-Host " MLOps Workshop - Cleanup" -ForegroundColor Red
Write-Host "============================================" -ForegroundColor Red
Write-Host ""
Write-Host "This will delete the following:" -ForegroundColor Yellow
Write-Host "  - Kind cluster: $ClusterName" -ForegroundColor Gray
Write-Host "  - All deployed resources (Airflow, MLflow, MinIO, PostgreSQL)" -ForegroundColor Gray
Write-Host "  - All persistent data" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Are you sure you want to proceed? (yes/no)"
if ($response -ne 'yes') {
    Write-Host "Cleanup cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Deleting Kind cluster..." -ForegroundColor Yellow
kind delete cluster --name $ClusterName

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Cleanup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "All resources have been deleted." -ForegroundColor Gray
Write-Host "Run deploy-all.ps1 to recreate the environment." -ForegroundColor Cyan

