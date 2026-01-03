"""
Model Training Pipeline for Telco Customer Churn
Trains multiple models and registers the best one in MLflow
"""

import os
import pandas as pd
import numpy as np
import boto3
from io import BytesIO
import logging
import json
from datetime import datetime
from typing import Dict, Any, Tuple

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow.mlflow.svc.cluster.local:5000')
EXPERIMENT_NAME = "telco-customer-churn"

def get_minio_client():
    """Create MinIO client connection"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )

def load_features() -> Tuple[pd.DataFrame, Dict]:
    """Load features from MinIO"""
    s3_client = get_minio_client()
    
    # Load feature data
    response = s3_client.get_object(
        Bucket='data-lake',
        Key='processed/features/telco_features_latest.parquet'
    )
    df = pd.read_parquet(BytesIO(response['Body'].read()))
    
    # Load schema
    schema_response = s3_client.get_object(
        Bucket='data-lake',
        Key='processed/features/feature_schema.json'
    )
    schema = json.loads(schema_response['Body'].read().decode('utf-8'))
    
    logger.info(f"Loaded {len(df)} feature records")
    return df, schema

def prepare_data(df: pd.DataFrame, schema: Dict) -> Tuple:
    """Prepare data for training"""
    feature_cols = schema['feature_columns']
    all_features = feature_cols['numeric_features'] + feature_cols['binary_features']
    
    X = df[all_features].copy()
    y = df[feature_cols['target']].copy()
    
    # Handle any remaining NaN values
    X = X.fillna(0)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale numeric features
    scaler = StandardScaler()
    numeric_cols = feature_cols['numeric_features']
    
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    
    X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
    X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    logger.info(f"Features: {len(all_features)}")
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, all_features

def get_models() -> Dict:
    """Define models to train"""
    return {
        'logistic_regression': LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        ),
        'random_forest': RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ),
        'gradient_boosting': GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
    }

def evaluate_model(model, X_test, y_test) -> Dict[str, float]:
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_prob)
    }
    
    return metrics

def train_and_log_model(
    model_name: str,
    model,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    scaler,
    feature_names: list
) -> Tuple[str, Dict]:
    """Train a model and log to MLflow"""
    
    with mlflow.start_run(run_name=model_name) as run:
        # Log parameters
        mlflow.log_param("model_type", model_name)
        mlflow.log_param("n_features", len(feature_names))
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        
        # Log model-specific parameters
        params = model.get_params()
        for key, value in params.items():
            if isinstance(value, (int, float, str, bool)):
                mlflow.log_param(key, value)
        
        # Train model
        logger.info(f"Training {model_name}...")
        model.fit(X_train, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
        mlflow.log_metric("cv_f1_mean", cv_scores.mean())
        mlflow.log_metric("cv_f1_std", cv_scores.std())
        
        # Evaluate on test set
        metrics = evaluate_model(model, X_test, y_test)
        
        for metric_name, metric_value in metrics.items():
            mlflow.log_metric(metric_name, metric_value)
        
        # Log feature importance if available
        if hasattr(model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            # Save feature importance
            importance_path = f"/tmp/{model_name}_feature_importance.csv"
            importance_df.to_csv(importance_path, index=False)
            mlflow.log_artifact(importance_path)
        
        # Log confusion matrix
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        cm_df = pd.DataFrame(cm, columns=['Pred_No', 'Pred_Yes'], index=['Actual_No', 'Actual_Yes'])
        cm_path = f"/tmp/{model_name}_confusion_matrix.csv"
        cm_df.to_csv(cm_path)
        mlflow.log_artifact(cm_path)
        
        # Log classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        report_path = f"/tmp/{model_name}_classification_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        mlflow.log_artifact(report_path)
        
        # Log model with signature
        from mlflow.models.signature import infer_signature
        signature = infer_signature(X_train, model.predict(X_train))
        
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            signature=signature,
            registered_model_name=f"telco-churn-{model_name}"
        )
        
        # Also save scaler
        scaler_path = "/tmp/scaler.joblib"
        joblib.dump(scaler, scaler_path)
        mlflow.log_artifact(scaler_path)
        
        logger.info(f"{model_name} - F1: {metrics['f1_score']:.4f}, AUC: {metrics['roc_auc']:.4f}")
        
        return run.info.run_id, metrics

def select_champion_model(results: Dict) -> str:
    """Select the best model based on F1 score"""
    best_model = max(results.items(), key=lambda x: x[1]['metrics']['f1_score'])
    logger.info(f"Champion model: {best_model[0]} with F1={best_model[1]['metrics']['f1_score']:.4f}")
    return best_model[0]

def promote_to_production(model_name: str, run_id: str):
    """Promote the best model to production stage"""
    client = MlflowClient()
    
    model_full_name = f"telco-churn-{model_name}"
    
    # Get latest version
    versions = client.search_model_versions(f"name='{model_full_name}'")
    if versions:
        latest_version = max(versions, key=lambda x: int(x.version))
        
        # Transition to production
        client.transition_model_version_stage(
            name=model_full_name,
            version=latest_version.version,
            stage="Production",
            archive_existing_versions=True
        )
        
        logger.info(f"Promoted {model_full_name} v{latest_version.version} to Production")

def run_training_pipeline():
    """Run the complete training pipeline"""
    # Setup MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Create or get experiment
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            EXPERIMENT_NAME,
            artifact_location="s3://mlflow-artifacts/experiments"
        )
    else:
        experiment_id = experiment.experiment_id
    
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    logger.info(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
    logger.info(f"Experiment: {EXPERIMENT_NAME}")
    
    # Load data
    df, schema = load_features()
    
    # Prepare data
    X_train, X_test, y_train, y_test, scaler, feature_names = prepare_data(df, schema)
    
    # Train models
    models = get_models()
    results = {}
    
    for model_name, model in models.items():
        run_id, metrics = train_and_log_model(
            model_name, model,
            X_train, X_test, y_train, y_test,
            scaler, feature_names
        )
        results[model_name] = {
            'run_id': run_id,
            'metrics': metrics
        }
    
    # Select and promote champion
    champion = select_champion_model(results)
    promote_to_production(champion, results[champion]['run_id'])
    
    # Save training summary to MinIO
    s3_client = get_minio_client()
    summary = {
        'timestamp': datetime.utcnow().isoformat(),
        'experiment': EXPERIMENT_NAME,
        'champion_model': champion,
        'results': {
            name: {
                'run_id': data['run_id'],
                'metrics': data['metrics']
            }
            for name, data in results.items()
        }
    }
    
    s3_client.put_object(
        Bucket='mlflow-artifacts',
        Key=f'training_summaries/training_summary_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
        Body=json.dumps(summary, indent=2),
        ContentType='application/json'
    )
    
    logger.info("Training pipeline completed successfully!")
    return results, champion

if __name__ == "__main__":
    run_training_pipeline()

