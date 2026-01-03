"""
DAG 05: Full ML Pipeline (End-to-End)
Orchestrates the complete MLOps workflow from data to deployment
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import logging

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
    '05_full_pipeline',
    default_args=default_args,
    description='Complete MLOps pipeline: Data -> Features -> Training -> Deployment',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
    tags=['mlops', 'pipeline', 'end-to-end'],
)


def log_pipeline_start():
    """Log pipeline start"""
    logger.info("=" * 50)
    logger.info("STARTING FULL ML PIPELINE")
    logger.info("=" * 50)
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    return {'status': 'started', 'timestamp': datetime.utcnow().isoformat()}


def log_pipeline_complete(**context):
    """Log pipeline completion"""
    ti = context['ti']
    start_info = ti.xcom_pull(task_ids='start_pipeline')
    
    logger.info("=" * 50)
    logger.info("ML PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 50)
    logger.info(f"Started: {start_info['timestamp']}")
    logger.info(f"Completed: {datetime.utcnow().isoformat()}")
    
    return {'status': 'completed', 'timestamp': datetime.utcnow().isoformat()}


# Tasks
start_task = PythonOperator(
    task_id='start_pipeline',
    python_callable=log_pipeline_start,
    dag=dag,
)

trigger_ingestion = TriggerDagRunOperator(
    task_id='trigger_data_ingestion',
    trigger_dag_id='01_data_ingestion',
    wait_for_completion=True,
    poke_interval=30,
    dag=dag,
)

trigger_features = TriggerDagRunOperator(
    task_id='trigger_feature_engineering',
    trigger_dag_id='02_feature_engineering',
    wait_for_completion=True,
    poke_interval=30,
    dag=dag,
)

trigger_training = TriggerDagRunOperator(
    task_id='trigger_model_training',
    trigger_dag_id='03_model_training',
    wait_for_completion=True,
    poke_interval=60,
    dag=dag,
)

trigger_evaluation = TriggerDagRunOperator(
    task_id='trigger_model_evaluation',
    trigger_dag_id='04_model_evaluation',
    wait_for_completion=True,
    poke_interval=30,
    dag=dag,
)

complete_task = PythonOperator(
    task_id='complete_pipeline',
    python_callable=log_pipeline_complete,
    dag=dag,
)

# Pipeline flow
start_task >> trigger_ingestion >> trigger_features >> trigger_training >> trigger_evaluation >> complete_task

