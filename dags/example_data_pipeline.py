"""
Example Data Pipeline DAG for MLOps Workshop
Demonstrates MinIO/S3 integration with Airflow
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os

default_args = {
    'owner': 'mlops-workshop',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}


def upload_to_minio(**context):
    """
    Upload sample data to MinIO
    """
    import boto3
    from botocore.client import Config
    import json
    
    # Get MinIO credentials from environment
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000')
    access_key = os.getenv('AWS_ACCESS_KEY_ID', 'mlops-access-key')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'mlops-secret-key-12345')
    
    # Create S3 client for MinIO
    s3_client = boto3.client(
        's3',
        endpoint_url=minio_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # Create sample data
    execution_date = context['execution_date'].strftime('%Y-%m-%d')
    sample_data = {
        'execution_date': execution_date,
        'pipeline': 'data_pipeline',
        'records_processed': 1000,
        'status': 'success'
    }
    
    # Upload to MinIO
    bucket_name = 'data-lake'
    object_key = f'pipeline-runs/{execution_date}/metadata.json'
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=json.dumps(sample_data),
        ContentType='application/json'
    )
    
    print(f"Uploaded data to s3://{bucket_name}/{object_key}")
    return object_key


def list_minio_objects(**context):
    """
    List objects in MinIO bucket
    """
    import boto3
    from botocore.client import Config
    
    minio_endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000')
    access_key = os.getenv('AWS_ACCESS_KEY_ID', 'mlops-access-key')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'mlops-secret-key-12345')
    
    s3_client = boto3.client(
        's3',
        endpoint_url=minio_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    # List objects
    response = s3_client.list_objects_v2(
        Bucket='data-lake',
        Prefix='pipeline-runs/'
    )
    
    objects = response.get('Contents', [])
    print(f"Found {len(objects)} objects in data-lake bucket:")
    for obj in objects:
        print(f"  - {obj['Key']} ({obj['Size']} bytes)")
    
    return len(objects)


with DAG(
    'data_pipeline_minio',
    default_args=default_args,
    description='Data pipeline demonstrating MinIO/S3 integration',
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'minio', 'data-pipeline'],
) as dag:
    
    # Task 1: Check MinIO connection
    check_minio = BashOperator(
        task_id='check_minio_connection',
        bash_command='curl -s $MINIO_ENDPOINT/minio/health/live && echo "MinIO is healthy" || echo "MinIO check failed"',
    )
    
    # Task 2: Upload data to MinIO
    upload = PythonOperator(
        task_id='upload_to_minio',
        python_callable=upload_to_minio,
        provide_context=True,
    )
    
    # Task 3: List objects
    list_objects = PythonOperator(
        task_id='list_minio_objects',
        python_callable=list_minio_objects,
        provide_context=True,
    )
    
    # Task 4: Complete
    complete = BashOperator(
        task_id='pipeline_complete',
        bash_command='echo "Data pipeline completed at $(date)"',
    )
    
    check_minio >> upload >> list_objects >> complete

