import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")

app = Celery("api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# TODO: remove once RabbitMQ broker is configured
app.conf.task_always_eager = True
