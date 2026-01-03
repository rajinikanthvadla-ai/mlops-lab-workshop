"""
Data Download Script for Telco Customer Churn Dataset
Source: IBM Sample Data Sets (Kaggle verified)
"""

import os
import boto3
import pandas as pd
from io import StringIO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telco Customer Churn Dataset URL (IBM Watson Analytics Sample Data)
DATASET_URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"

def get_minio_client():
    """Create MinIO client connection"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )

def download_and_upload_data():
    """Download Telco Churn dataset and upload to MinIO"""
    logger.info("Downloading Telco Customer Churn dataset from IBM...")
    
    # Download dataset
    df = pd.read_csv(DATASET_URL)
    logger.info(f"Downloaded {len(df)} records with {len(df.columns)} columns")
    
    # Display dataset info
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Target distribution:\n{df['Churn'].value_counts()}")
    
    # Connect to MinIO
    s3_client = get_minio_client()
    
    # Ensure bucket exists
    bucket_name = 'data-lake'
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except:
        s3_client.create_bucket(Bucket=bucket_name)
        logger.info(f"Created bucket: {bucket_name}")
    
    # Upload raw data
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key='raw/telco_churn/telco_customer_churn.csv',
        Body=csv_buffer.getvalue(),
        ContentType='text/csv'
    )
    logger.info("Uploaded raw data to MinIO: data-lake/raw/telco_churn/telco_customer_churn.csv")
    
    # Also save dataset info
    info = {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'target': 'Churn',
        'source': 'IBM Watson Analytics Sample Data',
        'url': DATASET_URL
    }
    
    import json
    s3_client.put_object(
        Bucket=bucket_name,
        Key='raw/telco_churn/metadata.json',
        Body=json.dumps(info, indent=2),
        ContentType='application/json'
    )
    logger.info("Uploaded metadata to MinIO")
    
    return df

def validate_data(df: pd.DataFrame) -> bool:
    """Validate downloaded data"""
    required_columns = ['customerID', 'Churn', 'tenure', 'MonthlyCharges', 'TotalCharges']
    
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    
    if len(df) < 1000:
        logger.error(f"Dataset too small: {len(df)} records")
        return False
    
    logger.info("Data validation passed!")
    return True

if __name__ == "__main__":
    df = download_and_upload_data()
    validate_data(df)

