"""
Data Ingestion Pipeline DAG for MLOps Workshop
Demonstrates MinIO/S3 integration for data lake operations
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os
import json

default_args = {
    'owner': 'mlops-workshop',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}


def generate_sample_data(**context):
    """Generate sample data for ingestion"""
    import random
    
    execution_date = context['ds']
    
    # Generate sample records
    records = []
    for i in range(100):
        record = {
            'id': f"record_{i}_{execution_date}",
            'timestamp': datetime.now().isoformat(),
            'value': random.uniform(0, 100),
            'category': random.choice(['A', 'B', 'C', 'D']),
            'status': random.choice(['active', 'inactive', 'pending'])
        }
        records.append(record)
    
    print(f"Generated {len(records)} sample records")
    return {'records_count': len(records), 'execution_date': execution_date}


def upload_to_minio(**context):
    """Upload data to MinIO data lake"""
    import json
    
    ti = context['ti']
    data_info = ti.xcom_pull(task_ids='generate_data')
    execution_date = context['ds']
    
    try:
        import boto3
        from botocore.client import Config
        
        # Get MinIO credentials
        minio_endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000')
        access_key = os.getenv('AWS_ACCESS_KEY_ID', 'mlops-access-key')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', 'mlops-secret-key-12345')
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=minio_endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        # Upload metadata
        bucket = 'data-lake'
        key = f"raw-data/{execution_date}/metadata.json"
        
        metadata = {
            'execution_date': execution_date,
            'records_count': data_info['records_count'],
            'pipeline': 'data_ingestion',
            'timestamp': datetime.now().isoformat()
        }
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        print(f"Uploaded to s3://{bucket}/{key}")
        return {'bucket': bucket, 'key': key, 'success': True}
        
    except ImportError:
        print("boto3 not available, skipping upload")
        return {'success': False, 'error': 'boto3 not installed'}
    except Exception as e:
        print(f"Upload failed: {e}")
        return {'success': False, 'error': str(e)}


def validate_upload(**context):
    """Validate the uploaded data"""
    ti = context['ti']
    upload_result = ti.xcom_pull(task_ids='upload_to_minio')
    
    if upload_result.get('success'):
        print(f"Upload validated: s3://{upload_result['bucket']}/{upload_result['key']}")
        return True
    else:
        print(f"Upload validation failed: {upload_result.get('error', 'Unknown error')}")
        return False


with DAG(
    'data_ingestion_pipeline',
    default_args=default_args,
    description='Data ingestion pipeline with MinIO integration',
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'minio', 'data-lake', 'ingestion'],
) as dag:
    
    start = BashOperator(
        task_id='start',
        bash_command='echo "Starting data ingestion at $(date)"',
    )
    
    generate = PythonOperator(
        task_id='generate_data',
        python_callable=generate_sample_data,
        provide_context=True,
    )
    
    upload = PythonOperator(
        task_id='upload_to_minio',
        python_callable=upload_to_minio,
        provide_context=True,
    )
    
    validate = PythonOperator(
        task_id='validate_upload',
        python_callable=validate_upload,
        provide_context=True,
    )
    
    complete = BashOperator(
        task_id='complete',
        bash_command='echo "Data ingestion completed at $(date)"',
    )
    
    start >> generate >> upload >> validate >> complete

