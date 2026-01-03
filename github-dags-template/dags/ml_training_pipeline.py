"""
ML Training Pipeline DAG for MLOps Workshop
This DAG demonstrates a complete ML training workflow with MLflow integration
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
    'retry_delay': timedelta(minutes=5),
}


def prepare_data(**context):
    """Prepare and validate data for training"""
    import random
    
    # Simulate data preparation
    num_samples = random.randint(1000, 5000)
    num_features = random.randint(10, 50)
    
    data_info = {
        'num_samples': num_samples,
        'num_features': num_features,
        'data_version': context['ds'],
        'status': 'prepared'
    }
    
    print(f"Data prepared: {num_samples} samples, {num_features} features")
    return data_info


def train_model(**context):
    """Train ML model and log to MLflow"""
    import random
    
    ti = context['ti']
    data_info = ti.xcom_pull(task_ids='prepare_data')
    
    # Simulate training
    learning_rate = random.uniform(0.001, 0.1)
    epochs = random.randint(10, 100)
    batch_size = random.choice([16, 32, 64, 128])
    
    # Simulate metrics
    accuracy = random.uniform(0.75, 0.98)
    loss = random.uniform(0.01, 0.25)
    f1_score = random.uniform(0.70, 0.95)
    
    model_info = {
        'learning_rate': learning_rate,
        'epochs': epochs,
        'batch_size': batch_size,
        'accuracy': accuracy,
        'loss': loss,
        'f1_score': f1_score,
        'data_samples': data_info['num_samples']
    }
    
    # Log to MLflow if available
    try:
        import mlflow
        
        mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow.mlflow.svc.cluster.local:5000')
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("ml-training-pipeline")
        
        with mlflow.start_run(run_name=f"training-{context['ds']}"):
            # Log parameters
            mlflow.log_param("learning_rate", learning_rate)
            mlflow.log_param("epochs", epochs)
            mlflow.log_param("batch_size", batch_size)
            mlflow.log_param("data_samples", data_info['num_samples'])
            mlflow.log_param("data_features", data_info['num_features'])
            
            # Log metrics
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("loss", loss)
            mlflow.log_metric("f1_score", f1_score)
            
            # Log tags
            mlflow.set_tag("pipeline", "airflow")
            mlflow.set_tag("execution_date", context['ds'])
            mlflow.set_tag("dag_id", context['dag'].dag_id)
            
            print(f"Logged to MLflow: accuracy={accuracy:.4f}, loss={loss:.4f}")
            
    except ImportError:
        print("MLflow not available, skipping logging")
    except Exception as e:
        print(f"MLflow logging failed: {e}")
    
    print(f"Model trained: accuracy={accuracy:.4f}, loss={loss:.4f}, f1={f1_score:.4f}")
    return model_info


def evaluate_model(**context):
    """Evaluate model and decide on deployment"""
    ti = context['ti']
    model_info = ti.xcom_pull(task_ids='train_model')
    
    accuracy_threshold = 0.80
    
    if model_info['accuracy'] >= accuracy_threshold:
        decision = "PROMOTE"
        print(f"Model PASSED evaluation (accuracy={model_info['accuracy']:.4f} >= {accuracy_threshold})")
    else:
        decision = "REJECT"
        print(f"Model FAILED evaluation (accuracy={model_info['accuracy']:.4f} < {accuracy_threshold})")
    
    return {
        'decision': decision,
        'accuracy': model_info['accuracy'],
        'threshold': accuracy_threshold
    }


with DAG(
    'ml_training_pipeline',
    default_args=default_args,
    description='Complete ML training pipeline with MLflow integration',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'mlflow', 'training', 'ml'],
) as dag:
    
    start = BashOperator(
        task_id='start_pipeline',
        bash_command='echo "Starting ML Training Pipeline at $(date)"',
    )
    
    prepare = PythonOperator(
        task_id='prepare_data',
        python_callable=prepare_data,
        provide_context=True,
    )
    
    train = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
        provide_context=True,
    )
    
    evaluate = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
        provide_context=True,
    )
    
    complete = BashOperator(
        task_id='complete_pipeline',
        bash_command='echo "ML Training Pipeline completed at $(date)"',
    )
    
    start >> prepare >> train >> evaluate >> complete

