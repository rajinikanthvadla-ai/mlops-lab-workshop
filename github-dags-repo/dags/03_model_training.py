"""
DAG 03: Model Training Pipeline
Trains multiple models and registers the best one in MLflow
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import logging
import os

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'mlops-workshop',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    '03_model_training',
    default_args=default_args,
    description='Train ML models for churn prediction',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'training', 'mlflow'],
)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow.mlflow.svc.cluster.local:5000')
EXPERIMENT_NAME = "telco-customer-churn"


def load_features():
    """Load features from MinIO"""
    import boto3
    import pandas as pd
    from io import BytesIO
    import json
    
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    # Load features
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
    
    # Save for next tasks
    df.to_parquet('/tmp/features.parquet', index=False)
    with open('/tmp/schema.json', 'w') as f:
        json.dump(schema, f)
    
    logger.info(f"Loaded {len(df)} feature records")
    return {'rows': len(df), 'churn_rate': schema['churn_rate']}


def prepare_data():
    """Prepare training and test datasets"""
    import pandas as pd
    import json
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import joblib
    
    df = pd.read_parquet('/tmp/features.parquet')
    with open('/tmp/schema.json', 'r') as f:
        schema = json.load(f)
    
    feature_cols = schema['feature_columns']
    all_features = feature_cols['numeric_features'] + feature_cols['binary_features']
    
    X = df[all_features].fillna(0)
    y = df[feature_cols['target']]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale numeric features
    scaler = StandardScaler()
    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()
    
    X_train_scaled[feature_cols['numeric_features']] = scaler.fit_transform(
        X_train[feature_cols['numeric_features']]
    )
    X_test_scaled[feature_cols['numeric_features']] = scaler.transform(
        X_test[feature_cols['numeric_features']]
    )
    
    # Save data
    X_train_scaled.to_parquet('/tmp/X_train.parquet')
    X_test_scaled.to_parquet('/tmp/X_test.parquet')
    y_train.to_frame().to_parquet('/tmp/y_train.parquet')
    y_test.to_frame().to_parquet('/tmp/y_test.parquet')
    joblib.dump(scaler, '/tmp/scaler.joblib')
    joblib.dump(all_features, '/tmp/feature_names.joblib')
    
    logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
    return {'train_size': len(X_train), 'test_size': len(X_test)}


def train_logistic_regression():
    """Train Logistic Regression model"""
    import pandas as pd
    import mlflow
    import mlflow.sklearn
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.model_selection import cross_val_score
    import joblib
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    # Load data
    X_train = pd.read_parquet('/tmp/X_train.parquet')
    X_test = pd.read_parquet('/tmp/X_test.parquet')
    y_train = pd.read_parquet('/tmp/y_train.parquet').iloc[:, 0]
    y_test = pd.read_parquet('/tmp/y_test.parquet').iloc[:, 0]
    scaler = joblib.load('/tmp/scaler.joblib')
    feature_names = joblib.load('/tmp/feature_names.joblib')
    
    with mlflow.start_run(run_name='logistic_regression') as run:
        model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
        
        mlflow.log_param("model_type", "logistic_regression")
        mlflow.log_param("n_features", len(feature_names))
        
        # Train
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_prob)
        }
        
        for name, value in metrics.items():
            mlflow.log_metric(name, value)
        
        # CV
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
        mlflow.log_metric("cv_f1_mean", cv_scores.mean())
        
        # Log model
        mlflow.sklearn.log_model(
            model, "model",
            registered_model_name="telco-churn-logistic_regression"
        )
        
        # Save scaler
        joblib.dump(scaler, '/tmp/lr_scaler.joblib')
        mlflow.log_artifact('/tmp/lr_scaler.joblib')
        
        logger.info(f"Logistic Regression - F1: {metrics['f1_score']:.4f}, AUC: {metrics['roc_auc']:.4f}")
        
    return metrics


def train_random_forest():
    """Train Random Forest model"""
    import pandas as pd
    import mlflow
    import mlflow.sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.model_selection import cross_val_score
    import joblib
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    X_train = pd.read_parquet('/tmp/X_train.parquet')
    X_test = pd.read_parquet('/tmp/X_test.parquet')
    y_train = pd.read_parquet('/tmp/y_train.parquet').iloc[:, 0]
    y_test = pd.read_parquet('/tmp/y_test.parquet').iloc[:, 0]
    scaler = joblib.load('/tmp/scaler.joblib')
    feature_names = joblib.load('/tmp/feature_names.joblib')
    
    with mlflow.start_run(run_name='random_forest') as run:
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        mlflow.log_param("model_type", "random_forest")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_prob)
        }
        
        for name, value in metrics.items():
            mlflow.log_metric(name, value)
        
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
        mlflow.log_metric("cv_f1_mean", cv_scores.mean())
        
        # Log feature importance
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        importance_df.to_csv('/tmp/rf_importance.csv', index=False)
        mlflow.log_artifact('/tmp/rf_importance.csv')
        
        mlflow.sklearn.log_model(
            model, "model",
            registered_model_name="telco-churn-random_forest"
        )
        
        mlflow.log_artifact('/tmp/scaler.joblib')
        
        logger.info(f"Random Forest - F1: {metrics['f1_score']:.4f}, AUC: {metrics['roc_auc']:.4f}")
        
    return metrics


def train_gradient_boosting():
    """Train Gradient Boosting model"""
    import pandas as pd
    import mlflow
    import mlflow.sklearn
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    from sklearn.model_selection import cross_val_score
    import joblib
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    
    X_train = pd.read_parquet('/tmp/X_train.parquet')
    X_test = pd.read_parquet('/tmp/X_test.parquet')
    y_train = pd.read_parquet('/tmp/y_train.parquet').iloc[:, 0]
    y_test = pd.read_parquet('/tmp/y_test.parquet').iloc[:, 0]
    feature_names = joblib.load('/tmp/feature_names.joblib')
    
    with mlflow.start_run(run_name='gradient_boosting') as run:
        model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        mlflow.log_param("model_type", "gradient_boosting")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("learning_rate", 0.1)
        
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_prob)
        }
        
        for name, value in metrics.items():
            mlflow.log_metric(name, value)
        
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
        mlflow.log_metric("cv_f1_mean", cv_scores.mean())
        
        mlflow.sklearn.log_model(
            model, "model",
            registered_model_name="telco-churn-gradient_boosting"
        )
        
        mlflow.log_artifact('/tmp/scaler.joblib')
        
        logger.info(f"Gradient Boosting - F1: {metrics['f1_score']:.4f}, AUC: {metrics['roc_auc']:.4f}")
        
    return metrics


def select_champion(**context):
    """Select the best model and promote to production"""
    import mlflow
    from mlflow.tracking import MlflowClient
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    
    # Get metrics from upstream tasks
    ti = context['ti']
    lr_metrics = ti.xcom_pull(task_ids='train_logistic_regression')
    rf_metrics = ti.xcom_pull(task_ids='train_random_forest')
    gb_metrics = ti.xcom_pull(task_ids='train_gradient_boosting')
    
    results = {
        'logistic_regression': lr_metrics,
        'random_forest': rf_metrics,
        'gradient_boosting': gb_metrics
    }
    
    # Select best by F1 score
    best_model = max(results.items(), key=lambda x: x[1]['f1_score'] if x[1] else 0)
    champion_name = best_model[0]
    
    logger.info(f"Champion model: {champion_name} with F1={best_model[1]['f1_score']:.4f}")
    
    # Promote to production
    model_full_name = f"telco-churn-{champion_name}"
    
    try:
        versions = client.search_model_versions(f"name='{model_full_name}'")
        if versions:
            latest_version = max(versions, key=lambda x: int(x.version))
            client.transition_model_version_stage(
                name=model_full_name,
                version=latest_version.version,
                stage="Production",
                archive_existing_versions=True
            )
            logger.info(f"Promoted {model_full_name} v{latest_version.version} to Production")
    except Exception as e:
        logger.error(f"Failed to promote model: {e}")
    
    return {'champion': champion_name, 'metrics': best_model[1]}


# Define tasks
load_task = PythonOperator(
    task_id='load_features',
    python_callable=load_features,
    dag=dag,
)

prepare_task = PythonOperator(
    task_id='prepare_data',
    python_callable=prepare_data,
    dag=dag,
)

train_lr_task = PythonOperator(
    task_id='train_logistic_regression',
    python_callable=train_logistic_regression,
    dag=dag,
)

train_rf_task = PythonOperator(
    task_id='train_random_forest',
    python_callable=train_random_forest,
    dag=dag,
)

train_gb_task = PythonOperator(
    task_id='train_gradient_boosting',
    python_callable=train_gradient_boosting,
    dag=dag,
)

select_task = PythonOperator(
    task_id='select_champion',
    python_callable=select_champion,
    dag=dag,
)

# Dependencies
load_task >> prepare_task >> [train_lr_task, train_rf_task, train_gb_task] >> select_task

