import os
from urllib.parse import quote
from celery import Celery
from src.common.settings import required
from src.inference.service import process
from src.persistence.db import rows

app = Celery("pucpr", broker=f"amqp://poc:{quote(required('RABBITMQ_PASSWORD'), safe='')}@{os.getenv('RABBITMQ_HOST', 'rabbitmq')}:5672//")
app.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1,
                task_ignore_result=True, broker_connection_retry_on_startup=True,
                task_publish_retry=False, broker_connection_timeout=5)


@app.task(name="predict", autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=3)
def predict(job_id):
    process(job_id)


def recover():
    for row in rows("SELECT id FROM planning.prediction_jobs WHERE status IN ('PENDING','RUNNING') ORDER BY requested_at LIMIT 100"):
        predict.delay(str(row["id"]))
