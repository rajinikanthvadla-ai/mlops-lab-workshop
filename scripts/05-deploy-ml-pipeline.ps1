# MLOps Workshop - Deploy ML Pipeline Components
# This script deploys Redis, Model Serving API, and Frontend Dashboard

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploying ML Pipeline Components" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check cluster is running
$clusterExists = kind get clusters 2>$null | Select-String "mlops-workshop"
if (-not $clusterExists) {
    Write-Host "ERROR: Kind cluster 'mlops-workshop' not found!" -ForegroundColor Red
    Write-Host "Run .\scripts\01-create-cluster.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[1/4] Deploying Redis (Feature Store Online Cache)..." -ForegroundColor Yellow
kubectl apply -f k8s/redis/

Write-Host ""
Write-Host "[2/4] Building Model Serving API Docker Image..." -ForegroundColor Yellow

# Check if Docker is running
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    exit 1
}

# Build the FastAPI serving image
Write-Host "Building churn-prediction-api image..." -ForegroundColor Gray
docker build -t churn-prediction-api:latest ./src/serving/

# Load image into Kind cluster
Write-Host "Loading image into Kind cluster..." -ForegroundColor Gray
kind load docker-image churn-prediction-api:latest --name mlops-workshop

Write-Host ""
Write-Host "[3/4] Deploying Model Serving API..." -ForegroundColor Yellow
kubectl apply -f k8s/model-serving/

Write-Host ""
Write-Host "[4/4] Building and Deploying Frontend Dashboard..." -ForegroundColor Yellow

# Build frontend image
Write-Host "Building churn-dashboard image..." -ForegroundColor Gray
docker build -t churn-dashboard:latest ./src/frontend/

# Load image into Kind cluster
Write-Host "Loading image into Kind cluster..." -ForegroundColor Gray
kind load docker-image churn-dashboard:latest --name mlops-workshop

# Deploy frontend
kubectl apply -f k8s/frontend/

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ML Pipeline Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Waiting for pods to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check pod status
Write-Host ""
Write-Host "Pod Status:" -ForegroundColor Cyan
kubectl get pods -n mlflow

Write-Host ""
Write-Host "Access URLs (after port-forwarding):" -ForegroundColor Cyan
Write-Host "  Model API:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Dashboard:  http://localhost:3000" -ForegroundColor White

Write-Host ""
Write-Host "To set up port forwarding, run:" -ForegroundColor Yellow
Write-Host "  kubectl port-forward svc/churn-prediction-api 8000:8000 -n mlflow" -ForegroundColor Gray
Write-Host "  kubectl port-forward svc/churn-dashboard 3000:80 -n mlflow" -ForegroundColor Gray

