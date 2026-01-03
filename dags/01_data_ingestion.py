"""
DAG 01: Data Ingestion Pipeline
Downloads Telco Customer Churn dataset from IBM and uploads to MinIO
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import logging

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
    '01_data_ingestion',
    default_args=default_args,
    description='Download and ingest Telco Customer Churn dataset',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'data', 'ingestion'],
)


def download_dataset():
    """Download Telco Churn dataset from IBM GitHub"""
    import pandas as pd
    
    DATASET_URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
    
    logger.info(f"Downloading dataset from {DATASET_URL}")
    df = pd.read_csv(DATASET_URL)
    
    logger.info(f"Downloaded {len(df)} records with columns: {list(df.columns)}")
    logger.info(f"Target distribution:\n{df['Churn'].value_counts().to_dict()}")
    
    # Save locally for next task
    df.to_csv('/tmp/telco_churn_raw.csv', index=False)
    
    return {
        'rows': len(df),
        'columns': len(df.columns),
        'churn_rate': float((df['Churn'] == 'Yes').mean())
    }


def validate_data():
    """Validate the downloaded dataset"""
    import pandas as pd
    
    df = pd.read_csv('/tmp/telco_churn_raw.csv')
    
    required_columns = ['customerID', 'Churn', 'tenure', 'MonthlyCharges', 'TotalCharges']
    
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    if len(df) < 1000:
        raise ValueError(f"Dataset too small: {len(df)} records (minimum: 1000)")
    
    # Check for too many nulls
    null_pct = df.isnull().sum() / len(df)
    high_null_cols = null_pct[null_pct > 0.5].index.tolist()
    if high_null_cols:
        logger.warning(f"Columns with >50% nulls: {high_null_cols}")
    
    logger.info("Data validation passed!")
    return {'status': 'valid', 'rows': len(df)}


def upload_to_minio():
    """Upload validated data to MinIO"""
    import boto3
    import pandas as pd
    from io import StringIO
    import json
    from datetime import datetime
    import os
    
    # MinIO configuration
    s3_client = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )
    
    bucket_name = 'data-lake'
    
    # Ensure bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except:
        s3_client.create_bucket(Bucket=bucket_name)
        logger.info(f"Created bucket: {bucket_name}")
    
    # Read data
    df = pd.read_csv('/tmp/telco_churn_raw.csv')
    
    # Upload raw data
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    # Upload timestamped version
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f'raw/telco_churn/telco_customer_churn_{timestamp}.csv',
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    
    # Upload latest version
    csv_buffer.seek(0)
    s3_client.put_object(
        Bucket=bucket_name,
        Key='raw/telco_churn/telco_customer_churn.csv',
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    
    # Upload metadata
    metadata = {
        'source': 'IBM Watson Analytics Sample Data',
        'url': 'https://github.com/IBM/telco-customer-churn-on-icp4d',
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'ingestion_timestamp': datetime.utcnow().isoformat(),
        'target_column': 'Churn'
    }
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key='raw/telco_churn/metadata.json',
        Body=json.dumps(metadata, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Uploaded {len(df)} records to MinIO: {bucket_name}/raw/telco_churn/")
    
    return {'bucket': bucket_name, 'key': 'raw/telco_churn/telco_customer_churn.csv', 'rows': len(df)}


# Define tasks
download_task = PythonOperator(
    task_id='download_dataset',
    python_callable=download_dataset,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag,
)

upload_task = PythonOperator(
    task_id='upload_to_minio',
    python_callable=upload_to_minio,
    dag=dag,
)

cleanup_task = BashOperator(
    task_id='cleanup_temp_files',
    bash_command='rm -f /tmp/telco_churn_raw.csv',
    dag=dag,
)

# Task dependencies
download_task >> validate_task >> upload_task >> cleanup_task

