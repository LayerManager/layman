from celery import Celery
from celery.contrib import abortable
from .settings import *


def make_celery(app):
    celery_app = Celery(
        'layman',
        backend=LAYMAN_REDIS_URL,
        broker=LAYMAN_REDIS_URL,
        include=[
            'layman.db.tasks',
            'layman.filesystem.tasks',
            'layman.geoserver.tasks',
        ],
        # http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html
        broker_transport_options={
            'visibility_timeout': 3600, # 1 hour
            'fanout_prefix': True,
            'fanout_patterns': True,
        },
        # https://stackoverflow.com/a/38267978
        task_track_started=True,
    )
    # celery.conf.update(app.config)
    # celery_app.conf.update(
    #     task_serializer='pickle',
    #     accept_content=['pickle', 'json'],
    #     result_serializer='pickle',
    # )

    class Task(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    class AbortableTask(abortable.AbortableTask):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = Task
    celery_app.AbortableTask = AbortableTask
    return celery_app