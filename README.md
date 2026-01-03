# MLOps Lab Workshop

A complete local MLOps environment running on Kubernetes (Kind) for teaching and learning MLOps/AIOps concepts.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Kind Cluster (3 Nodes)                              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Control Plane Node                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────────────────────┐      ┌────────────────────────────────┐      │
│  │       Worker Node 1      │      │         Worker Node 2          │      │
│  └──────────────────────────┘      └────────────────────────────────┘      │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Airflow    │  │    MLflow    │  │    MinIO     │  │  PostgreSQL  │   │
│  │   :8080      │  │    :5000     │  │    :9001     │  │    :5432     │   │
│  │              │  │              │  │              │  │              │   │
│  │ • Webserver  │  │ • Tracking   │  │ • Artifacts  │  │ • MLflow DB  │   │
│  │ • Scheduler  │  │ • Registry   │  │ • Data Lake  │  │ • Airflow DB │   │
│  │ • Git-sync   │  │ • Artifacts  │  │ • Logs       │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │           │
│         └─────────────────┴─────────────────┴─────────────────┘           │
│                           Internal Network                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                     ┌───────────────┼───────────────┐
                     ▼               ▼               ▼
              localhost:8080   localhost:5000   localhost:9001
                (Airflow)        (MLflow)         (MinIO)
```

## 📦 Components

| Component | Description | Access URL | Credentials |
|-----------|-------------|------------|-------------|
| **Apache Airflow** | Workflow orchestration | http://localhost:8080 | admin / admin123 |
| **MLflow** | ML experiment tracking & model registry | http://localhost:5000 | No auth |
| **MinIO** | S3-compatible object storage | http://localhost:9001 | minioadmin / minioadmin123 |
| **PostgreSQL** | Backend database | Internal only | - |

## ✅ Prerequisites

- **Docker Desktop** - Running with sufficient resources (4GB+ RAM recommended)
- **Kind** - Kubernetes IN Docker
- **kubectl** - Kubernetes CLI
- **Helm** (optional)

### Install Prerequisites (Windows)

```powershell
# Install Kind
winget install Kubernetes.kind
# OR
choco install kind

# Install kubectl
winget install Kubernetes.kubectl
# OR
choco install kubernetes-cli
```

## 🚀 Quick Start

### One-Command Deployment

```powershell
# Navigate to project directory
cd F:\MLOPS-Fundamentals\mlops-lab-workshop

# Deploy everything
.\scripts\deploy-all.ps1
```

### Step-by-Step Deployment

```powershell
# Step 1: Create 3-node Kind cluster
.\scripts\01-create-cluster.ps1

# Step 2: Deploy PostgreSQL and MinIO
.\scripts\02-deploy-infrastructure.ps1

# Step 3: Deploy MLflow
.\scripts\03-deploy-mlflow.ps1

# Step 4: Deploy Airflow
.\scripts\04-deploy-airflow.ps1
```

## 🔗 Access Services

After deployment:

| Service | URL | Login |
|---------|-----|-------|
| **Airflow UI** | http://localhost:8080 | admin / admin123 |
| **MLflow UI** | http://localhost:5000 | (no login) |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |

## 📝 Git-Sync for DAGs

Airflow can automatically sync DAGs from a GitHub repository.

### Enable Git-Sync

```powershell
# Enable Git-sync with your GitHub repository
.\scripts\enable-git-sync.ps1 -GitRepoUrl "https://github.com/your-org/your-dags-repo.git"

# With custom branch and DAGs folder
.\scripts\enable-git-sync.ps1 `
    -GitRepoUrl "https://github.com/your-org/your-dags-repo.git" `
    -Branch "main" `
    -DagsFolder "dags"
```

### Create Your DAGs Repository

Use the template in `github-dags-template/` to create your own DAGs repository:

```
your-dags-repo/
├── dags/
│   ├── hello_world.py
│   ├── ml_training_pipeline.py
│   └── data_ingestion_pipeline.py
└── README.md
```

### How Git-Sync Works

1. Git-sync container runs alongside Airflow
2. Pulls from your repository every 60 seconds
3. DAGs are automatically available in Airflow
4. No restart required!

## 💻 Using MLflow

### From Inside the Cluster (DAGs)

```python
import mlflow
import os

mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
mlflow.set_tracking_uri(mlflow_uri)
mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_metric("accuracy", 0.95)
```

### From Local Machine

```python
import os
import mlflow

# Set MinIO credentials for artifact storage
os.environ["AWS_ACCESS_KEY_ID"] = "mlops-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "mlops-secret-key-12345"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("local-experiment")

with mlflow.start_run():
    mlflow.log_param("model_type", "random_forest")
    mlflow.log_metric("accuracy", 0.92)
```

## 📦 Using MinIO

### Via Python (boto3)

```python
import boto3
from botocore.client import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='mlops-access-key',
    aws_secret_access_key='mlops-secret-key-12345',
    config=Config(signature_version='s3v4')
)

# List buckets
for bucket in s3.list_buckets()['Buckets']:
    print(bucket['Name'])

# Upload file
s3.upload_file('local_file.csv', 'data-lake', 'uploads/file.csv')
```

### Via AWS CLI

```powershell
aws configure set aws_access_key_id mlops-access-key
aws configure set aws_secret_access_key mlops-secret-key-12345

# List buckets
aws --endpoint-url http://localhost:9000 s3 ls

# Upload file
aws --endpoint-url http://localhost:9000 s3 cp myfile.txt s3://data-lake/
```

## 🛠️ Useful Commands

### Check Status

```powershell
.\scripts\status.ps1

# Or manually
kubectl get pods -A
```

### View Logs

```powershell
# Airflow scheduler
kubectl logs -f deployment/airflow-scheduler -n airflow

# MLflow
kubectl logs -f deployment/mlflow -n mlflow

# MinIO
kubectl logs -f deployment/minio -n minio
```

### Restart Components

```powershell
# Restart Airflow
kubectl rollout restart deployment/airflow-webserver -n airflow
kubectl rollout restart deployment/airflow-scheduler -n airflow

# Restart MLflow
kubectl rollout restart deployment/mlflow -n mlflow
```

## 🧹 Cleanup

```powershell
.\scripts\cleanup.ps1
```

## 🔧 Troubleshooting

### Pods Not Starting

```powershell
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

### Database Connection Issues

```powershell
# Check PostgreSQL
kubectl get pods -n postgres
kubectl logs deployment/postgres -n postgres
```

### Git-Sync Not Working

```powershell
# Check git-sync logs
kubectl logs deployment/airflow-scheduler -n airflow -c git-sync
```

### Port Already in Use

```powershell
# Check what's using the port
netstat -ano | findstr :8080
```

## 📁 Project Structure

```
mlops-lab-workshop/
├── kind-cluster-config.yaml     # Kind 3-node cluster config
├── k8s/                         # Kubernetes manifests
│   ├── namespaces/
│   ├── postgres/
│   ├── minio/
│   ├── mlflow/
│   └── airflow/
├── scripts/                     # Deployment scripts
│   ├── 01-create-cluster.ps1
│   ├── 02-deploy-infrastructure.ps1
│   ├── 03-deploy-mlflow.ps1
│   ├── 04-deploy-airflow.ps1
│   ├── deploy-all.ps1
│   ├── enable-git-sync.ps1
│   ├── status.ps1
│   └── cleanup.ps1
├── dags/                        # Example DAGs (local reference)
├── github-dags-template/        # Template for GitHub DAGs repo
└── README.md
```

## 🎓 Workshop Exercises

### Exercise 1: Your First DAG
1. Open Airflow UI at http://localhost:8080
2. Find the `hello_world` DAG
3. Enable and trigger it
4. Check the logs

### Exercise 2: MLflow Experiment Tracking
1. Open MLflow UI at http://localhost:5000
2. Create a new experiment
3. Run the `mlflow_integration_example` DAG
4. View the logged metrics

### Exercise 3: Data Pipeline with MinIO
1. Open MinIO Console at http://localhost:9001
2. Browse the `data-lake` bucket
3. Run the `data_ingestion_pipeline` DAG
4. Check new data in MinIO

### Exercise 4: Enable Git-Sync
1. Fork the `github-dags-template` to your GitHub
2. Run `enable-git-sync.ps1` with your repo URL
3. Modify a DAG in GitHub
4. Watch it appear in Airflow!

## 📚 Key Credentials Summary

| Service | Username | Password |
|---------|----------|----------|
| Airflow | admin | admin123 |
| MinIO Console | minioadmin | minioadmin123 |
| MinIO Access Key | mlops-access-key | mlops-secret-key-12345 |
| PostgreSQL | postgres | postgresadmin123 |

## 📄 License

MIT License - Feel free to use for educational purposes.

---

**Happy Learning! 🚀**
