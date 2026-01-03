"""
DAG 04: Model Evaluation and A/B Testing Analysis
Evaluates model performance and updates A/B test configuration
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
    '04_model_evaluation',
    default_args=default_args,
    description='Evaluate models and update A/B testing configuration',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'evaluation', 'ab-testing'],
)

MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow.mlflow.svc.cluster.local:5000')


def get_production_models():
    """Get all production models from MLflow"""
    import mlflow
    from mlflow.tracking import MlflowClient
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()
    
    model_names = [
        "telco-churn-logistic_regression",
        "telco-churn-random_forest",
        "telco-churn-gradient_boosting"
    ]
    
    production_models = []
    
    for name in model_names:
        try:
            versions = client.search_model_versions(f"name='{name}'")
            prod_versions = [v for v in versions if v.current_stage == "Production"]
            
            if prod_versions:
                v = prod_versions[0]
                production_models.append({
                    'name': name,
                    'version': v.version,
                    'run_id': v.run_id,
                    'stage': 'Production'
                })
                logger.info(f"Found production model: {name} v{v.version}")
        except Exception as e:
            logger.warning(f"Could not check {name}: {e}")
    
    return production_models


def compare_models(**context):
    """Compare production models using test data"""
    import pandas as pd
    import mlflow
    import mlflow.sklearn
    from sklearn.metrics import f1_score, roc_auc_score
    from io import BytesIO
    import boto3
    
    ti = context['ti']
    production_models = ti.xcom_pull(task_ids='get_production_models')
    
    if not production_models:
        logger.warning("No production models found")
        return {'status': 'no_models'}
    
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Load test data
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    response = s3_client.get_object(
        Bucket='data-lake',
        Key='processed/features/telco_features_latest.parquet'
    )
    df = pd.read_parquet(BytesIO(response['Body'].read()))
    
    # Get feature columns
    import json
    schema_response = s3_client.get_object(
        Bucket='data-lake',
        Key='processed/features/feature_schema.json'
    )
    schema = json.loads(schema_response['Body'].read().decode('utf-8'))
    feature_cols = schema['feature_columns']
    all_features = feature_cols['numeric_features'] + feature_cols['binary_features']
    
    # Sample test data
    test_df = df.sample(frac=0.2, random_state=42)
    X_test = test_df[all_features].fillna(0)
    y_test = test_df[feature_cols['target']]
    
    results = {}
    
    for model_info in production_models:
        try:
            model_uri = f"models:/{model_info['name']}/Production"
            model = mlflow.sklearn.load_model(model_uri)
            
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]
            
            results[model_info['name']] = {
                'f1_score': float(f1_score(y_test, y_pred)),
                'roc_auc': float(roc_auc_score(y_test, y_prob)),
                'version': model_info['version']
            }
            
            logger.info(f"{model_info['name']}: F1={results[model_info['name']]['f1_score']:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to evaluate {model_info['name']}: {e}")
    
    return results


def update_ab_config(**context):
    """Update A/B testing configuration based on model performance"""
    import json
    import boto3
    from datetime import datetime
    
    ti = context['ti']
    comparison_results = ti.xcom_pull(task_ids='compare_models')
    
    if not comparison_results or comparison_results.get('status') == 'no_models':
        logger.warning("No comparison results, keeping current config")
        return {'status': 'no_change'}
    
    # Sort by F1 score
    sorted_models = sorted(
        comparison_results.items(),
        key=lambda x: x[1]['f1_score'],
        reverse=True
    )
    
    if len(sorted_models) < 2:
        logger.warning("Need at least 2 models for A/B testing")
        return {'status': 'insufficient_models'}
    
    champion = sorted_models[0]
    challenger = sorted_models[1]
    
    # Calculate traffic split based on performance difference
    f1_diff = champion[1]['f1_score'] - challenger[1]['f1_score']
    
    if f1_diff > 0.1:
        # Big difference - champion gets most traffic
        champion_weight = 0.9
        challenger_weight = 0.1
    elif f1_diff > 0.05:
        # Moderate difference
        champion_weight = 0.8
        challenger_weight = 0.2
    else:
        # Close performance - more exploration
        champion_weight = 0.6
        challenger_weight = 0.4
    
    ab_config = {
        'champion': {
            'name': champion[0],
            'weight': champion_weight,
            'metrics': champion[1]
        },
        'challenger': {
            'name': challenger[0],
            'weight': challenger_weight,
            'metrics': challenger[1]
        },
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Save to MinIO
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    s3_client.put_object(
        Bucket='mlflow-artifacts',
        Key='ab_config/current_config.json',
        Body=json.dumps(ab_config, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Updated A/B config: {champion[0]}={champion_weight:.0%}, {challenger[0]}={challenger_weight:.0%}")
    
    return ab_config


def generate_report(**context):
    """Generate evaluation report"""
    import json
    import boto3
    from datetime import datetime
    
    ti = context['ti']
    production_models = ti.xcom_pull(task_ids='get_production_models')
    comparison_results = ti.xcom_pull(task_ids='compare_models')
    ab_config = ti.xcom_pull(task_ids='update_ab_config')
    
    report = {
        'generated_at': datetime.utcnow().isoformat(),
        'production_models': production_models,
        'model_comparison': comparison_results,
        'ab_configuration': ab_config,
        'summary': {
            'total_models': len(production_models) if production_models else 0,
            'best_model': max(comparison_results.items(), key=lambda x: x[1]['f1_score'])[0] if comparison_results and comparison_results.get('status') != 'no_models' else None
        }
    }
    
    # Save report
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    s3_client.put_object(
        Bucket='mlflow-artifacts',
        Key=f'reports/evaluation_report_{timestamp}.json',
        Body=json.dumps(report, indent=2),
        ContentType='application/json'
    )
    
    logger.info("Generated evaluation report")
    
    return report


# Define tasks
get_models_task = PythonOperator(
    task_id='get_production_models',
    python_callable=get_production_models,
    dag=dag,
)

compare_task = PythonOperator(
    task_id='compare_models',
    python_callable=compare_models,
    dag=dag,
)

update_ab_task = PythonOperator(
    task_id='update_ab_config',
    python_callable=update_ab_config,
    dag=dag,
)

report_task = PythonOperator(
    task_id='generate_report',
    python_callable=generate_report,
    dag=dag,
)

# Dependencies
get_models_task >> compare_task >> update_ab_task >> report_task

