# ============================================================================
# MLOps Workshop - Step 1: Create Kind Cluster
# ============================================================================
# This script creates a 3-node Kind cluster for the MLOps workshop
# Prerequisites: Docker Desktop running, Kind installed
# ============================================================================

param(
    [string]$ClusterName = "mlops-workshop"
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MLOps Workshop - Create Kind Cluster" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "  ✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Kind is installed
Write-Host "[2/4] Checking Kind..." -ForegroundColor Yellow
try {
    $kindVersion = kind version
    Write-Host "  ✓ Kind version: $kindVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Kind is not installed. Please install Kind first." -ForegroundColor Red
    Write-Host "  Run: choco install kind  OR  winget install Kubernetes.kind" -ForegroundColor Yellow
    exit 1
}

# Check if cluster already exists
Write-Host "[3/4] Checking for existing cluster..." -ForegroundColor Yellow
$existingCluster = kind get clusters 2>$null | Where-Object { $_ -eq $ClusterName }
if ($existingCluster) {
    Write-Host "  ! Cluster '$ClusterName' already exists." -ForegroundColor Yellow
    $response = Read-Host "  Do you want to delete and recreate it? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "  Deleting existing cluster..." -ForegroundColor Yellow
        kind delete cluster --name $ClusterName
        Write-Host "  ✓ Cluster deleted" -ForegroundColor Green
    } else {
        Write-Host "  Keeping existing cluster. Exiting." -ForegroundColor Yellow
        exit 0
    }
}

# Create the cluster
Write-Host "[4/4] Creating 3-node Kind cluster..." -ForegroundColor Yellow
$configPath = Join-Path $PSScriptRoot "..\kind-cluster-config.yaml"
Write-Host "  Using config: $configPath" -ForegroundColor Gray

try {
    kind create cluster --config $configPath --wait 5m
    Write-Host ""
    Write-Host "  ✓ Cluster created successfully!" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to create cluster" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Verify cluster
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Cluster Verification" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
kubectl cluster-info --context kind-$ClusterName
Write-Host ""
Write-Host "Nodes:" -ForegroundColor Yellow
kubectl get nodes

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Cluster Ready!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Run 02-deploy-infrastructure.ps1" -ForegroundColor Cyan

