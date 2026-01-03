"""
Hello World DAG for MLOps Workshop
Simple DAG to verify Airflow is working correctly
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'mlops-workshop',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def print_context(**context):
    """Print execution context"""
    print(f"Execution Date: {context['ds']}")
    print(f"DAG ID: {context['dag'].dag_id}")
    print(f"Task ID: {context['task'].task_id}")
    print("Hello from MLOps Workshop!")
    return "Success"


with DAG(
    'hello_world',
    default_args=default_args,
    description='Simple hello world DAG',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'workshop'],
) as dag:
    
    task1 = BashOperator(
        task_id='print_date',
        bash_command='echo "Current date: $(date)"',
    )
    
    task2 = PythonOperator(
        task_id='hello_python',
        python_callable=print_context,
        provide_context=True,
    )
    
    task3 = BashOperator(
        task_id='goodbye',
        bash_command='echo "DAG completed successfully!"',
    )
    
    task1 >> task2 >> task3

