"""
Feature Engineering for Telco Customer Churn
Transforms raw data into ML-ready features
"""

import os
import pandas as pd
import numpy as np
import boto3
from io import StringIO, BytesIO
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_minio_client():
    """Create MinIO client connection"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://minio.minio.svc.cluster.local:9000'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin123'),
        region_name='us-east-1'
    )

def load_raw_data() -> pd.DataFrame:
    """Load raw data from MinIO"""
    s3_client = get_minio_client()
    
    response = s3_client.get_object(
        Bucket='data-lake',
        Key='raw/telco_churn/telco_customer_churn.csv'
    )
    
    df = pd.read_csv(response['Body'])
    logger.info(f"Loaded {len(df)} records from MinIO")
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features for churn prediction
    """
    logger.info("Starting feature engineering...")
    
    # Create a copy
    data = df.copy()
    
    # 1. Clean TotalCharges (has some empty strings)
    data['TotalCharges'] = pd.to_numeric(data['TotalCharges'], errors='coerce')
    data['TotalCharges'].fillna(data['MonthlyCharges'], inplace=True)
    
    # 2. Create binary target
    data['churn_label'] = (data['Churn'] == 'Yes').astype(int)
    
    # 3. Tenure-based features
    data['tenure_months'] = data['tenure']
    data['tenure_years'] = data['tenure'] / 12
    data['is_new_customer'] = (data['tenure'] <= 6).astype(int)
    data['is_loyal_customer'] = (data['tenure'] >= 24).astype(int)
    
    # 4. Charge-based features
    data['monthly_charges'] = data['MonthlyCharges']
    data['total_charges'] = data['TotalCharges']
    data['avg_monthly_charge'] = data['TotalCharges'] / (data['tenure'] + 1)
    data['charge_per_tenure'] = data['MonthlyCharges'] / (data['tenure'] + 1)
    
    # 5. Service count features
    service_columns = ['PhoneService', 'MultipleLines', 'InternetService', 
                       'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                       'TechSupport', 'StreamingTV', 'StreamingMovies']
    
    data['total_services'] = 0
    for col in service_columns:
        if col in data.columns:
            data['total_services'] += (data[col].isin(['Yes', 'DSL', 'Fiber optic'])).astype(int)
    
    # 6. Contract type encoding
    data['contract_month_to_month'] = (data['Contract'] == 'Month-to-month').astype(int)
    data['contract_one_year'] = (data['Contract'] == 'One year').astype(int)
    data['contract_two_year'] = (data['Contract'] == 'Two year').astype(int)
    
    # 7. Payment method encoding
    data['payment_electronic'] = (data['PaymentMethod'] == 'Electronic check').astype(int)
    data['payment_auto'] = data['PaymentMethod'].str.contains('automatic', case=False).astype(int)
    
    # 8. Internet service encoding
    data['has_internet'] = (data['InternetService'] != 'No').astype(int)
    data['has_fiber'] = (data['InternetService'] == 'Fiber optic').astype(int)
    
    # 9. Demographics encoding
    data['is_senior'] = data['SeniorCitizen']
    data['has_partner'] = (data['Partner'] == 'Yes').astype(int)
    data['has_dependents'] = (data['Dependents'] == 'Yes').astype(int)
    
    # 10. Paperless billing
    data['paperless_billing'] = (data['PaperlessBilling'] == 'Yes').astype(int)
    
    # 11. Security features
    data['has_security'] = ((data['OnlineSecurity'] == 'Yes') | 
                            (data['OnlineBackup'] == 'Yes') |
                            (data['DeviceProtection'] == 'Yes')).astype(int)
    
    # 12. Support features
    data['has_support'] = (data['TechSupport'] == 'Yes').astype(int)
    
    # 13. Streaming features
    data['has_streaming'] = ((data['StreamingTV'] == 'Yes') | 
                             (data['StreamingMovies'] == 'Yes')).astype(int)
    
    # 14. Risk score (heuristic)
    data['risk_score'] = (
        data['contract_month_to_month'] * 3 +
        data['payment_electronic'] * 2 +
        data['is_new_customer'] * 2 +
        (1 - data['has_support']) * 1 +
        data['has_fiber'] * 1 -
        data['is_loyal_customer'] * 2
    )
    
    logger.info(f"Created {len([c for c in data.columns if c not in df.columns])} new features")
    
    return data

def get_feature_columns() -> dict:
    """Return feature column definitions"""
    return {
        'numeric_features': [
            'tenure_months', 'tenure_years', 'monthly_charges', 'total_charges',
            'avg_monthly_charge', 'charge_per_tenure', 'total_services', 'risk_score'
        ],
        'binary_features': [
            'is_new_customer', 'is_loyal_customer', 'contract_month_to_month',
            'contract_one_year', 'contract_two_year', 'payment_electronic',
            'payment_auto', 'has_internet', 'has_fiber', 'is_senior',
            'has_partner', 'has_dependents', 'paperless_billing',
            'has_security', 'has_support', 'has_streaming'
        ],
        'target': 'churn_label',
        'id': 'customerID'
    }

def save_features(df: pd.DataFrame):
    """Save engineered features to MinIO"""
    s3_client = get_minio_client()
    
    feature_cols = get_feature_columns()
    all_features = feature_cols['numeric_features'] + feature_cols['binary_features']
    
    # Create feature dataframe
    feature_df = df[['customerID'] + all_features + ['churn_label']].copy()
    
    # Add metadata
    feature_df['feature_timestamp'] = datetime.utcnow().isoformat()
    
    # Save as parquet for efficiency
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
    
    # Also save latest version
    parquet_buffer.seek(0)
    s3_client.put_object(
        Bucket='data-lake',
        Key='processed/features/telco_features_latest.parquet',
        Body=parquet_buffer.getvalue(),
        ContentType='application/octet-stream'
    )
    
    # Save feature schema
    schema = {
        'feature_columns': feature_cols,
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
    logger.info(f"Features: {all_features}")
    
    return feature_df

def run_feature_pipeline():
    """Run the complete feature engineering pipeline"""
    # Load raw data
    raw_df = load_raw_data()
    
    # Engineer features
    feature_df = engineer_features(raw_df)
    
    # Save features
    saved_df = save_features(feature_df)
    
    return saved_df

if __name__ == "__main__":
    run_feature_pipeline()

