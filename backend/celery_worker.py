# backend/celery_worker.py
from celery import Celery

celery = Celery(
    'parking_app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['backend.tasks.background']  # Explicitly include your tasks module
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)