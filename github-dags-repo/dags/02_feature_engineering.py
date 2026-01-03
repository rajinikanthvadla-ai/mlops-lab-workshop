"""
DAG 02: Feature Engineering Pipeline
Transforms raw data into ML-ready features
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
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    '02_feature_engineering',
    default_args=default_args,
    description='Transform raw data into ML features',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'features', 'engineering'],
)


def load_raw_data():
    """Load raw data from MinIO"""
    import boto3
    import pandas as pd
    
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    response = s3_client.get_object(
        Bucket='data-lake',
        Key='raw/telco_churn/telco_customer_churn.csv'
    )
    
    df = pd.read_csv(response['Body'])
    df.to_csv('/tmp/raw_data.csv', index=False)
    
    logger.info(f"Loaded {len(df)} records from MinIO")
    return {'rows': len(df)}


def engineer_features():
    """Create engineered features"""
    import pandas as pd
    import numpy as np
    
    df = pd.read_csv('/tmp/raw_data.csv')
    data = df.copy()
    
    # Clean TotalCharges
    data['TotalCharges'] = pd.to_numeric(data['TotalCharges'], errors='coerce')
    data['TotalCharges'].fillna(data['MonthlyCharges'], inplace=True)
    
    # Binary target
    data['churn_label'] = (data['Churn'] == 'Yes').astype(int)
    
    # Tenure features
    data['tenure_months'] = data['tenure']
    data['tenure_years'] = data['tenure'] / 12
    data['is_new_customer'] = (data['tenure'] <= 6).astype(int)
    data['is_loyal_customer'] = (data['tenure'] >= 24).astype(int)
    
    # Charge features
    data['monthly_charges'] = data['MonthlyCharges']
    data['total_charges'] = data['TotalCharges']
    data['avg_monthly_charge'] = data['TotalCharges'] / (data['tenure'] + 1)
    data['charge_per_tenure'] = data['MonthlyCharges'] / (data['tenure'] + 1)
    
    # Service count
    service_columns = ['PhoneService', 'MultipleLines', 'InternetService', 
                       'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                       'TechSupport', 'StreamingTV', 'StreamingMovies']
    
    data['total_services'] = 0
    for col in service_columns:
        if col in data.columns:
            data['total_services'] += (data[col].isin(['Yes', 'DSL', 'Fiber optic'])).astype(int)
    
    # Contract encoding
    data['contract_month_to_month'] = (data['Contract'] == 'Month-to-month').astype(int)
    data['contract_one_year'] = (data['Contract'] == 'One year').astype(int)
    data['contract_two_year'] = (data['Contract'] == 'Two year').astype(int)
    
    # Payment encoding
    data['payment_electronic'] = (data['PaymentMethod'] == 'Electronic check').astype(int)
    data['payment_auto'] = data['PaymentMethod'].str.contains('automatic', case=False).astype(int)
    
    # Internet encoding
    data['has_internet'] = (data['InternetService'] != 'No').astype(int)
    data['has_fiber'] = (data['InternetService'] == 'Fiber optic').astype(int)
    
    # Demographics
    data['is_senior'] = data['SeniorCitizen']
    data['has_partner'] = (data['Partner'] == 'Yes').astype(int)
    data['has_dependents'] = (data['Dependents'] == 'Yes').astype(int)
    
    # Other features
    data['paperless_billing'] = (data['PaperlessBilling'] == 'Yes').astype(int)
    data['has_security'] = ((data['OnlineSecurity'] == 'Yes') | 
                            (data['OnlineBackup'] == 'Yes') |
                            (data['DeviceProtection'] == 'Yes')).astype(int)
    data['has_support'] = (data['TechSupport'] == 'Yes').astype(int)
    data['has_streaming'] = ((data['StreamingTV'] == 'Yes') | 
                             (data['StreamingMovies'] == 'Yes')).astype(int)
    
    # Risk score
    data['risk_score'] = (
        data['contract_month_to_month'] * 3 +
        data['payment_electronic'] * 2 +
        data['is_new_customer'] * 2 +
        (1 - data['has_support']) * 1 +
        data['has_fiber'] * 1 -
        data['is_loyal_customer'] * 2
    )
    
    data.to_csv('/tmp/feature_data.csv', index=False)
    
    new_features = len([c for c in data.columns if c not in df.columns])
    logger.info(f"Created {new_features} new features")
    
    return {'original_cols': len(df.columns), 'new_cols': len(data.columns), 'new_features': new_features}


def save_features():
    """Save engineered features to MinIO"""
    import boto3
    import pandas as pd
    from io import BytesIO
    import json
    from datetime import datetime
    
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    df = pd.read_csv('/tmp/feature_data.csv')
    
    # Feature columns
    numeric_features = [
        'tenure_months', 'tenure_years', 'monthly_charges', 'total_charges',
        'avg_monthly_charge', 'charge_per_tenure', 'total_services', 'risk_score'
    ]
    binary_features = [
        'is_new_customer', 'is_loyal_customer', 'contract_month_to_month',
        'contract_one_year', 'contract_two_year', 'payment_electronic',
        'payment_auto', 'has_internet', 'has_fiber', 'is_senior',
        'has_partner', 'has_dependents', 'paperless_billing',
        'has_security', 'has_support', 'has_streaming'
    ]
    
    all_features = numeric_features + binary_features
    feature_df = df[['customerID'] + all_features + ['churn_label']].copy()
    feature_df['feature_timestamp'] = datetime.utcnow().isoformat()
    
    # Save as parquet
    parquet_buffer = BytesIO()
    feature_df.to_parquet(parquet_buffer, index=False)
    parquet_buffer.seek(0)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    s3_client.put_object(
        Bucket='data-lake',
        Key=f'processed/features/telco_features_{timestamp}.parquet',
        Body=parquet_buffer.getvalue(),
        ContentType='application/octet-stream'
    )
    
    parquet_buffer.seek(0)
    s3_client.put_object(
        Bucket='data-lake',
        Key='processed/features/telco_features_latest.parquet',
        Body=parquet_buffer.getvalue(),
        ContentType='application/octet-stream'
    )
    
    # Save schema
    schema = {
        'feature_columns': {
            'numeric_features': numeric_features,
            'binary_features': binary_features,
            'target': 'churn_label',
            'id': 'customerID'
        },
        'total_records': len(feature_df),
        'created_at': datetime.utcnow().isoformat(),
        'churn_rate': float(feature_df['churn_label'].mean())
    }
    
    s3_client.put_object(
        Bucket='data-lake',
        Key='processed/features/feature_schema.json',
        Body=json.dumps(schema, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Saved {len(feature_df)} feature records to MinIO")
    return {'rows': len(feature_df), 'features': len(all_features)}


# Define tasks
load_task = PythonOperator(
    task_id='load_raw_data',
    python_callable=load_raw_data,
    dag=dag,
)

engineer_task = PythonOperator(
    task_id='engineer_features',
    python_callable=engineer_features,
    dag=dag,
)

save_task = PythonOperator(
    task_id='save_features',
    python_callable=save_features,
    dag=dag,
)

# Task dependencies
load_task >> engineer_task >> save_task

