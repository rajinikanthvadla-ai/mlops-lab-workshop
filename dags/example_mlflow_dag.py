"""
Example Airflow DAG for MLOps Workshop
This DAG demonstrates integration between Airflow and MLflow
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import os

# Default arguments for the DAG
default_args = {
    'owner': 'mlops-workshop',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def train_model(**context):
    """
    Example training function that logs to MLflow
    """
    import mlflow
    import random
    
    # Get MLflow tracking URI from environment
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow.mlflow.svc.cluster.local:5000')
    mlflow.set_tracking_uri(mlflow_uri)
    
    # Set experiment
    mlflow.set_experiment("airflow-workshop-experiment")
    
    with mlflow.start_run(run_name=f"airflow-run-{context['execution_date']}"):
        # Log parameters
        learning_rate = random.uniform(0.01, 0.1)
        epochs = random.randint(10, 100)
        
        mlflow.log_param("learning_rate", learning_rate)
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("model_type", "demo_model")
        
        # Simulate training and log metrics
        accuracy = random.uniform(0.7, 0.99)
        loss = random.uniform(0.01, 0.3)
        
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("loss", loss)
        
        # Log a tag
        mlflow.set_tag("triggered_by", "airflow")
        mlflow.set_tag("dag_id", context['dag'].dag_id)
        
        print(f"Model trained with accuracy: {accuracy:.4f}, loss: {loss:.4f}")
        return {"accuracy": accuracy, "loss": loss}


def validate_model(**context):
    """
    Example validation function
    """
    ti = context['ti']
    training_results = ti.xcom_pull(task_ids='train_model')
    
    if training_results and training_results.get('accuracy', 0) > 0.8:
        print("Model validation PASSED!")
        return True
    else:
        print("Model validation FAILED - accuracy below threshold")
        return False


# Define the DAG
with DAG(
    'mlops_training_pipeline',
    default_args=default_args,
    description='MLOps training pipeline with MLflow integration',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'mlflow', 'training'],
) as dag:
    
    # Task 1: Check MLflow connection
    check_mlflow = BashOperator(
        task_id='check_mlflow_connection',
        bash_command='curl -s -o /dev/null -w "%{http_code}" $MLFLOW_TRACKING_URI/health || echo "MLflow not reachable"',
    )
    
    # Task 2: Train model
    train = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
        provide_context=True,
    )
    
    # Task 3: Validate model
    validate = PythonOperator(
        task_id='validate_model',
        python_callable=validate_model,
        provide_context=True,
    )
    
    # Task 4: Log completion
    complete = BashOperator(
        task_id='pipeline_complete',
        bash_command='echo "MLOps training pipeline completed successfully at $(date)"',
    )
    
    # Define task dependencies
    check_mlflow >> train >> validate >> complete

