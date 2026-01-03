# MLOps Workshop - Port Forwarding Script
# Sets up all port forwards for local access

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setting Up Port Forwards" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Starting port-forwards in background..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop all port-forwards" -ForegroundColor Gray
Write-Host ""

# Create jobs for each port-forward
$jobs = @()

Write-Host "  Airflow UI     -> http://localhost:8080" -ForegroundColor Green
$jobs += Start-Job -ScriptBlock { kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow 2>$null }

Write-Host "  MLflow UI      -> http://localhost:5000" -ForegroundColor Green
$jobs += Start-Job -ScriptBlock { kubectl port-forward svc/mlflow 5000:5000 -n mlflow 2>$null }

Write-Host "  MinIO Console  -> http://localhost:9001" -ForegroundColor Green
$jobs += Start-Job -ScriptBlock { kubectl port-forward svc/minio 9000:9000 9001:9001 -n minio 2>$null }

Write-Host "  Model API      -> http://localhost:8000" -ForegroundColor Green
$jobs += Start-Job -ScriptBlock { kubectl port-forward svc/churn-prediction-api 8000:8000 -n mlflow 2>$null }

Write-Host "  Dashboard      -> http://localhost:3000" -ForegroundColor Green
$jobs += Start-Job -ScriptBlock { kubectl port-forward svc/churn-dashboard 3000:80 -n mlflow 2>$null }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All Services Available!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor White
Write-Host "  Airflow:    http://localhost:8080  (admin/admin123)" -ForegroundColor Gray
Write-Host "  MLflow:     http://localhost:5000" -ForegroundColor Gray
Write-Host "  MinIO:      http://localhost:9001  (minioadmin/minioadmin123)" -ForegroundColor Gray
Write-Host "  Model API:  http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  Dashboard:  http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Enter to stop all port-forwards..." -ForegroundColor Yellow

Read-Host

# Stop all jobs
Write-Host "Stopping port-forwards..." -ForegroundColor Yellow
$jobs | ForEach-Object { Stop-Job $_ }
$jobs | ForEach-Object { Remove-Job $_ }

Write-Host "Done!" -ForegroundColor Green

