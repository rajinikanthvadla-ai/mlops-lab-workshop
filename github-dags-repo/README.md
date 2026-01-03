# 🚀 MLOps Workshop - Airflow DAGs Repository

This repository contains Airflow DAGs for the MLOps Workshop's Customer Churn Prediction pipeline.

## 📋 DAGs Overview

| DAG | Schedule | Description |
|-----|----------|-------------|
| `01_data_ingestion` | Daily | Downloads IBM Telco Churn dataset, validates, uploads to MinIO |
| `02_feature_engineering` | Daily | Transforms raw data into 24 ML features |
| `03_model_training` | Weekly | Trains 3 models (LR, RF, GB), registers best in MLflow |
| `04_model_evaluation` | Daily | Compares models, updates A/B testing config |
| `05_full_pipeline` | Weekly | End-to-end orchestration of all DAGs |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AIRFLOW DAGs                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  01_data_ingestion ──► 02_feature_engineering ──►           │
│                                                              │
│  03_model_training ──► 04_model_evaluation                  │
│                                                              │
│  05_full_pipeline (orchestrates all above)                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │  MinIO  │         │ MLflow  │         │ Postgres │
    │(Storage)│         │(Tracking)│        │(Backend) │
    └─────────┘         └─────────┘         └─────────┘
```

## 📁 Repository Structure

```
mlops-workshop-dags/
├── dags/
│   ├── 01_data_ingestion.py      # Data download & upload
│   ├── 02_feature_engineering.py  # Feature transformation
│   ├── 03_model_training.py       # Model training & registry
│   ├── 04_model_evaluation.py     # Model comparison & A/B config
│   └── 05_full_pipeline.py        # End-to-end orchestration
└── README.md
```

## 🔧 Configuration

### Environment Variables

The DAGs expect these environment variables (set in Airflow):

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ENDPOINT` | `http://minio.minio.svc.cluster.local:9000` | MinIO service URL |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin123` | MinIO secret key |
| `MLFLOW_TRACKING_URI` | `http://mlflow.mlflow.svc.cluster.local:5000` | MLflow tracking URL |

### Required Python Packages

The Airflow workers need these packages:

```
pandas
numpy
scikit-learn
mlflow
boto3
pyarrow
```

## 🚀 Usage

### Manual Trigger

1. Open Airflow UI (http://localhost:8080)
2. Enable the desired DAG
3. Click "Trigger DAG" button

### Automatic Execution

DAGs run on their configured schedules:
- **Daily DAGs**: Run once per day
- **Weekly DAGs**: Run once per week

### Full Pipeline

To run the complete ML pipeline:
1. Enable `05_full_pipeline`
2. It will trigger all other DAGs in sequence

## 📊 Data Flow

```
IBM GitHub ──► MinIO (raw/) ──► Feature Engineering ──► MinIO (processed/)
                                       │
                                       ▼
                               Model Training
                                       │
                                       ▼
                            MLflow Model Registry
                                       │
                                       ▼
                            A/B Config Update
```

## 🔍 Monitoring

### Check DAG Status
```bash
kubectl logs deployment/airflow-scheduler -n airflow
```

### Check Git-Sync Status
```bash
kubectl logs deployment/airflow-scheduler -n airflow -c git-sync
```

### View in Airflow UI
- DAG runs: http://localhost:8080/home
- Task logs: Click on task in Grid/Graph view

## 📝 Adding New DAGs

1. Create a new `.py` file in the `dags/` folder
2. Follow the existing DAG structure
3. Commit and push to GitHub
4. DAG will auto-sync within 60 seconds

## 🐛 Troubleshooting

### DAGs not appearing?
```bash
# Check git-sync logs
kubectl logs deployment/airflow-scheduler -n airflow -c git-sync

# Check for Python syntax errors
kubectl logs deployment/airflow-scheduler -n airflow -c scheduler
```

### Task failures?
1. Check task logs in Airflow UI
2. Verify MinIO/MLflow connectivity
3. Check required Python packages are installed

---

**Part of MLOps Workshop** | Built for teaching production ML operations

