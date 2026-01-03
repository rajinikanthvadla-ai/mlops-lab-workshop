# ============================================================================
# MLOps Workshop - Deploy Everything
# ============================================================================
# This script runs all deployment steps in sequence
# Prerequisites: Docker Desktop running, Kind installed
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop",
    [string]$GitRepoUrl = "",
    [switch]$SkipClusterCreation
)

$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Magenta
Write-Host " MLOps Workshop - Full Deployment" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "This will deploy:" -ForegroundColor Yellow
Write-Host "  1. Kind Cluster (3 nodes)" -ForegroundColor Gray
Write-Host "  2. PostgreSQL Database" -ForegroundColor Gray
Write-Host "  3. MinIO Object Storage" -ForegroundColor Gray
Write-Host "  4. MLflow Tracking Server" -ForegroundColor Gray
Write-Host "  5. Apache Airflow" -ForegroundColor Gray
Write-Host ""

# Step 1: Create Cluster
if (-not $SkipClusterCreation) {
    Write-Host ""
    Write-Host "========== STEP 1: Create Cluster ==========" -ForegroundColor Magenta
    & "$scriptPath\01-create-cluster.ps1" -ClusterName $ClusterName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create cluster. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Step 2: Deploy Infrastructure
Write-Host ""
Write-Host "========== STEP 2: Deploy Infrastructure ==========" -ForegroundColor Magenta
& "$scriptPath\02-deploy-infrastructure.ps1" -ClusterName $ClusterName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to deploy infrastructure. Exiting." -ForegroundColor Red
    exit 1
}

# Wait a bit for infrastructure to stabilize
Write-Host ""
Write-Host "Waiting for infrastructure to stabilize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 3: Deploy MLflow
Write-Host ""
Write-Host "========== STEP 3: Deploy MLflow ==========" -ForegroundColor Magenta
& "$scriptPath\03-deploy-mlflow.ps1" -ClusterName $ClusterName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to deploy MLflow. Exiting." -ForegroundColor Red
    exit 1
}

# Step 4: Deploy Airflow
Write-Host ""
Write-Host "========== STEP 4: Deploy Airflow ==========" -ForegroundColor Magenta
& "$scriptPath\04-deploy-airflow.ps1" -ClusterName $ClusterName -GitRepoUrl $GitRepoUrl
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to deploy Airflow. Exiting." -ForegroundColor Red
    exit 1
}

# Final Status
Write-Host ""
Write-Host "============================================" -ForegroundColor Magenta
Write-Host " DEPLOYMENT COMPLETE!" -ForegroundColor Magenta
Write-Host "============================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "All Pods:" -ForegroundColor Yellow
kubectl get pods -A | Where-Object { $_ -match "airflow|mlflow|minio|postgres" }

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Access URLs" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Airflow UI:    http://localhost:8080" -ForegroundColor Cyan
Write-Host "               Username: admin / Password: admin123" -ForegroundColor Gray
Write-Host ""
Write-Host "MLflow UI:     http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "MinIO Console: http://localhost:9001" -ForegroundColor Cyan
Write-Host "               Username: minioadmin / Password: minioadmin123" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Architecture Overview" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  ┌─────────────────────────────────────────────────────┐" -ForegroundColor White
Write-Host "  │                   Kind Cluster                      │" -ForegroundColor White
Write-Host "  │  ┌─────────────────────────────────────────────┐   │" -ForegroundColor White
Write-Host "  │  │              Control Plane                   │   │" -ForegroundColor White
Write-Host "  │  └─────────────────────────────────────────────┘   │" -ForegroundColor White
Write-Host "  │  ┌──────────────────┐  ┌──────────────────────┐   │" -ForegroundColor White
Write-Host "  │  │    Worker 1       │  │      Worker 2        │   │" -ForegroundColor White
Write-Host "  │  └──────────────────┘  └──────────────────────┘   │" -ForegroundColor White
Write-Host "  │                                                     │" -ForegroundColor White
Write-Host "  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │" -ForegroundColor White
Write-Host "  │  │Airflow  │ │ MLflow  │ │ MinIO   │ │Postgres │  │" -ForegroundColor White
Write-Host "  │  │ :8080   │ │ :5000   │ │ :9001   │ │ :5432   │  │" -ForegroundColor White
Write-Host "  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │" -ForegroundColor White
Write-Host "  │       │           │           │           │        │" -ForegroundColor White
Write-Host "  │       └───────────┴───────────┴───────────┘        │" -ForegroundColor White
Write-Host "  │                   Internal Network                  │" -ForegroundColor White
Write-Host "  └─────────────────────────────────────────────────────┘" -ForegroundColor White
Write-Host ""
Write-Host "DAGs are synced from GitHub every 60 seconds." -ForegroundColor Yellow
Write-Host "Models logged in MLflow are stored in MinIO." -ForegroundColor Yellow

