# MLOps Workshop - Run ML Pipeline
# This script runs the data ingestion, feature engineering, and model training

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running ML Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    exit 1
}

# Create virtual environment if not exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install pandas numpy scikit-learn mlflow boto3 pyarrow --quiet

# Set environment variables for local development
$env:MINIO_ENDPOINT = "http://localhost:9000"
$env:MINIO_ACCESS_KEY = "minioadmin"
$env:MINIO_SECRET_KEY = "minioadmin123"
$env:MLFLOW_TRACKING_URI = "http://localhost:5000"

Write-Host ""
Write-Host "NOTE: This script requires port-forwarding to MinIO and MLflow" -ForegroundColor Yellow
Write-Host "Run these commands in separate terminals:" -ForegroundColor Yellow
Write-Host "  kubectl port-forward svc/minio 9000:9000 -n minio" -ForegroundColor Gray
Write-Host "  kubectl port-forward svc/mlflow 5000:5000 -n mlflow" -ForegroundColor Gray

Write-Host ""
Write-Host "Press Enter when port-forwarding is ready..." -ForegroundColor Cyan
Read-Host

Write-Host ""
Write-Host "[1/3] Running Data Ingestion..." -ForegroundColor Yellow
python src/data/download_data.py

Write-Host ""
Write-Host "[2/3] Running Feature Engineering..." -ForegroundColor Yellow
python src/features/feature_engineering.py

Write-Host ""
Write-Host "[3/3] Running Model Training..." -ForegroundColor Yellow
python src/training/train_model.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ML Pipeline Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Check MLflow UI at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "View experiments and registered models" -ForegroundColor Gray

