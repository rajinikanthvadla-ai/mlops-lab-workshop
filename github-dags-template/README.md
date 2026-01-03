# MLOps Workshop DAGs Repository

This repository contains Airflow DAGs for the MLOps Workshop. 
DAGs are automatically synced to Airflow using Git-sync.

## Repository Structure

```
├── dags/
│   ├── hello_world.py              # Simple test DAG
│   ├── ml_training_pipeline.py     # ML training with MLflow
│   └── data_ingestion_pipeline.py  # Data pipeline with MinIO
└── README.md
```

## DAGs

### hello_world
A simple DAG to verify Airflow is working correctly.

### ml_training_pipeline
Complete ML training workflow with:
- Data preparation
- Model training with parameter logging
- MLflow experiment tracking
- Model evaluation

### data_ingestion_pipeline
Data lake operations with:
- Sample data generation
- Upload to MinIO (S3-compatible)
- Data validation

## How It Works

1. This repository is configured in Airflow's Git-sync
2. Every 60 seconds, Git-sync pulls the latest changes
3. Airflow automatically picks up new/modified DAGs
4. No restart required!

## Adding New DAGs

1. Create a new Python file in the `dags/` folder
2. Define your DAG using standard Airflow patterns
3. Commit and push to this repository
4. Wait ~60 seconds for sync
5. Your DAG appears in Airflow UI!

## Environment Variables

These environment variables are available in DAGs:

- `MLFLOW_TRACKING_URI` - MLflow server URL
- `MINIO_ENDPOINT` - MinIO S3-compatible endpoint
- `AWS_ACCESS_KEY_ID` - MinIO access key
- `AWS_SECRET_ACCESS_KEY` - MinIO secret key

