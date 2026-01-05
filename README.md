# 🚀 MLOps Workshop - Production ML Pipeline

A complete, production-grade MLOps environment for teaching real-world machine learning operations. This workshop demonstrates an end-to-end ML pipeline with Customer Churn Prediction using industry-standard tools.

![Architecture](docs/architecture.png)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Components](#components)
- [ML Pipeline](#ml-pipeline)
- [Access URLs](#access-urls)
- [Workshop Guide](#workshop-guide)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This workshop provides a hands-on experience with:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Container Orchestration** | Kubernetes (Kind) | 3-node cluster for production-like environment |
| **Workflow Orchestration** | Apache Airflow | DAG-based ML pipeline automation |
| **Experiment Tracking** | MLflow | Model versioning, metrics, and registry |
| **Object Storage** | MinIO | S3-compatible data lake and artifact storage |
| **Database** | PostgreSQL | Backend for MLflow and Airflow |
| **Feature Store** | Redis | Online feature serving cache |
| **Model Serving** | FastAPI | REST API with A/B testing |
| **Frontend** | React + TailwindCSS | Real-time prediction dashboard |

### 🎓 Use Case: Telco Customer Churn Prediction

We use the **IBM Telco Customer Churn** dataset (verified, real-world data) to demonstrate:
- Data ingestion from external sources
- Feature engineering pipeline
- Multi-model training (Logistic Regression, Random Forest, Gradient Boosting)
- A/B testing between model versions
- Real-time prediction serving

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        KIND KUBERNETES CLUSTER                               │
│                     (1 Control Plane + 2 Workers)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   AIRFLOW    │───▶│    MINIO     │◀───│   MLFLOW     │                   │
│  │  Scheduler   │    │  Data Lake   │    │  Tracking    │                   │
│  │  Webserver   │    │  Artifacts   │    │  Registry    │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         │            ┌──────────────┐          │                            │
│         └───────────▶│  POSTGRESQL  │◀─────────┘                            │
│                      │   Backend    │                                        │
│                      └──────────────┘                                        │
│                             │                                                │
│  ┌──────────────────────────┴───────────────────────────┐                   │
│  │                  MODEL SERVING LAYER                  │                   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────┐  │                   │
│  │  │   FastAPI   │    │  A/B Router │    │  Redis   │  │                   │
│  │  │   /predict  │◀──▶│  80%/20%    │◀──▶│  Cache   │  │                   │
│  │  └─────────────┘    └─────────────┘    └──────────┘  │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                             │                                                │
│  ┌──────────────────────────┴───────────────────────────┐                   │
│  │              FRONTEND DASHBOARD (React)               │                   │
│  │  • Real-time Predictions  • A/B Test Visualization   │                   │
│  │  • Model Comparison       • Feature Importance       │                   │
│  └──────────────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

Before starting, ensure you have:

- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **kubectl** - [Install Guide](https://kubernetes.io/docs/tasks/tools/)
- **Kind** - [Install Guide](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** (for frontend development) - [Download](https://nodejs.org/)

### Windows Installation

```powershell
# Install Kind (using Chocolatey)
choco install kind -y

# Install kubectl
choco install kubernetes-cli -y

# Verify installations
kind version
kubectl version --client
docker version
```

## 🚀 Quick Start

### Step 1: Clone and Setup

```powershell
cd F:\MLOPS-Fundamentals\mlops-lab-workshop
```

### Step 2: Deploy Everything

```powershell
# Option A: Deploy all at once
.\scripts\deploy-all.ps1

# Option B: Step-by-step deployment
.\scripts\01-create-cluster.ps1       # Create Kind cluster
.\scripts\02-deploy-infrastructure.ps1 # Deploy MinIO, PostgreSQL
.\scripts\03-deploy-mlflow.ps1         # Deploy MLflow
.\scripts\04-deploy-airflow.ps1        # Deploy Airflow
.\scripts\05-deploy-ml-pipeline.ps1    # Deploy ML serving components
```

### Step 3: Access Services

```powershell
# Start all port-forwards
.\scripts\port-forward.ps1
```

### Step 4: Run ML Pipeline

```powershell
# Run the complete ML pipeline
.\scripts\06-run-ml-pipeline.ps1
```

## 📁 Project Structure

```
mlops-lab-workshop/
├── 📁 k8s/                          # Kubernetes manifests
│   ├── airflow/                     # Airflow deployment
│   ├── mlflow/                      # MLflow deployment
│   ├── minio/                       # MinIO (S3) deployment
│   ├── postgres/                    # PostgreSQL deployment
│   ├── redis/                       # Redis deployment
│   ├── model-serving/               # FastAPI model serving
│   ├── frontend/                    # React dashboard
│   └── namespaces/                  # Namespace definitions
│
├── 📁 src/                          # Source code
│   ├── data/                        # Data ingestion scripts
│   │   └── download_data.py
│   ├── features/                    # Feature engineering
│   │   └── feature_engineering.py
│   ├── training/                    # Model training
│   │   └── train_model.py
│   ├── serving/                     # FastAPI application
│   │   ├── app/
│   │   │   ├── main.py             # API endpoints
│   │   │   ├── predictor.py        # Model inference
│   │   │   └── ab_router.py        # A/B testing logic
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── frontend/                    # React dashboard
│       ├── src/
│       ├── package.json
│       └── Dockerfile
│
├── 📁 dags/                         # Airflow DAGs
│   ├── 01_data_ingestion.py        # Download & store data
│   ├── 02_feature_engineering.py   # Transform features
│   ├── 03_model_training.py        # Train & register models
│   ├── 04_model_evaluation.py      # Evaluate & update A/B
│   └── 05_full_pipeline.py         # End-to-end orchestration
│
├── 📁 scripts/                      # Deployment scripts
│   ├── deploy-all.ps1              # One-click deployment
│   ├── 01-create-cluster.ps1
│   ├── 02-deploy-infrastructure.ps1
│   ├── 03-deploy-mlflow.ps1
│   ├── 04-deploy-airflow.ps1
│   ├── 05-deploy-ml-pipeline.ps1
│   ├── 06-run-ml-pipeline.ps1
│   ├── port-forward.ps1            # Access all services
│   ├── status.ps1                  # Check cluster status
│   └── cleanup.ps1                 # Remove everything
│
├── 📁 github-dags-template/         # Template for GitHub DAGs repo
├── kind-cluster-config.yaml         # Kind cluster configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## 🔧 Components

### 1. Data Layer (MinIO)

MinIO provides S3-compatible storage for:
- **Raw Data**: `data-lake/raw/telco_churn/`
- **Processed Features**: `data-lake/processed/features/`
- **Model Artifacts**: `mlflow-artifacts/`

### 2. Feature Engineering

Transforms raw customer data into ML features:

| Feature Category | Examples |
|-----------------|----------|
| **Tenure** | `tenure_months`, `is_new_customer`, `is_loyal_customer` |
| **Charges** | `monthly_charges`, `avg_monthly_charge`, `charge_per_tenure` |
| **Services** | `total_services`, `has_internet`, `has_streaming` |
| **Contract** | `contract_month_to_month`, `payment_electronic` |
| **Risk** | `risk_score` (calculated heuristic) |

### 3. Model Training

Three models trained and compared:

| Model | Description | Typical AUC |
|-------|-------------|-------------|
| Logistic Regression | Baseline, interpretable | ~0.82 |
| Random Forest | Ensemble, good accuracy | ~0.85 |
| Gradient Boosting | Best performance | ~0.86 |

### 4. A/B Testing

- **Champion Model**: 80% traffic (best performer)
- **Challenger Model**: 20% traffic (experimental)
- Real-time metrics tracking
- Automatic promotion based on performance

### 5. Model Serving API

FastAPI endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Single customer prediction |
| `/predict/batch` | POST | Batch predictions |
| `/predict/explain` | POST | Prediction with feature importance |
| `/models` | GET | List deployed models |
| `/ab-stats` | GET | A/B testing statistics |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

### 6. Frontend Dashboard

React-based dashboard with:
- Real-time churn predictions
- Model performance comparison
- A/B test visualization
- Feature importance charts

## 🔄 ML Pipeline

### Airflow DAGs

| DAG | Schedule | Description |
|-----|----------|-------------|
| `01_data_ingestion` | Daily | Download dataset from IBM, upload to MinIO |
| `02_feature_engineering` | Daily | Transform raw data to features |
| `03_model_training` | Weekly | Train models, register in MLflow |
| `04_model_evaluation` | Daily | Compare models, update A/B config |
| `05_full_pipeline` | Weekly | End-to-end orchestration |

### Running the Pipeline

**Option 1: Via Airflow UI**
1. Open http://localhost:8080
2. Enable the `05_full_pipeline` DAG
3. Trigger manually or wait for schedule

**Option 2: Via Script**
```powershell
.\scripts\06-run-ml-pipeline.ps1
```

## 🌐 Access URLs

After running `.\scripts\port-forward.ps1`:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow UI** | http://localhost:8080 | `admin` / `admin123` |
| **MLflow UI** | http://localhost:5000 | (no auth) |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin123` |
| **Model API Docs** | http://localhost:8000/docs | (no auth) |
| **Dashboard** | http://localhost:3000 | (no auth) |

## 📚 Workshop Guide

### Module 1: Infrastructure Setup (30 min)
1. Create Kind cluster
2. Deploy MinIO and PostgreSQL
3. Explore Kubernetes resources

### Module 2: MLflow & Experiment Tracking (30 min)
1. Deploy MLflow
2. Run training script
3. Compare experiments in UI
4. Understand model registry

### Module 3: Data Pipeline (45 min)
1. Explore data ingestion DAG
2. Run feature engineering
3. Understand feature store concepts

### Module 4: Model Training & Registry (45 min)
1. Train multiple models
2. Compare metrics
3. Promote to production
4. Version management

### Module 5: Model Serving & A/B Testing (45 min)
1. Deploy FastAPI service
2. Make predictions
3. Understand A/B routing
4. Monitor performance

### Module 6: Frontend & Integration (30 min)
1. Explore dashboard
2. End-to-end prediction flow
3. Real-world scenarios

## 🔍 Troubleshooting

### Common Issues

**Pods not starting?**
```powershell
kubectl get pods -A
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

**MLflow not connecting to MinIO?**
```powershell
# Check MinIO is accessible
kubectl port-forward svc/minio 9000:9000 -n minio
# Test with aws cli
aws --endpoint-url http://localhost:9000 s3 ls
```

**Airflow DAGs not showing?**
```powershell
# Check DAG sync
kubectl logs deployment/airflow-scheduler -n airflow
```

**Model serving failing?**
```powershell
# Check if models are registered
kubectl port-forward svc/mlflow 5000:5000 -n mlflow
# Visit http://localhost:5000/#/models
```

### Reset Everything

```powershell
.\scripts\cleanup.ps1
.\scripts\deploy-all.ps1
```

## 📊 Dataset Information

**Telco Customer Churn Dataset**
- **Source**: IBM Watson Analytics Sample Data
- **Size**: 7,043 customers
- **Features**: 21 columns
- **Target**: Churn (Yes/No)
- **Churn Rate**: ~26.5%

## 🤝 Contributing

This is an educational project. Feel free to:
- Add new models
- Improve feature engineering
- Enhance the dashboard
- Add monitoring with Prometheus/Grafana

## 📄 License

MIT License - Use freely for educational purposes.

---

**Happy Learning! 🎓**

*Built for MLOps/AIOps Workshop - production ML to experienced professionals*
