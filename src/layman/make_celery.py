from celery import Celery
from celery.contrib import abortable
from layman import settings
from .util import get_modules_from_names


def make_celery(app):
    celery_app = Celery(
        'layman',
        backend=settings.LAYMAN_REDIS_URL,
        broker=settings.LAYMAN_REDIS_URL,
        include=get_task_modules(),
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


def get_task_modules():
    task_modules = []
    for publ_module in get_modules_from_names(settings.PUBLICATION_MODULES):
        for type_def in publ_module.PUBLICATION_TYPES.values():
            task_modules += type_def['task_modules']
    return task_modules

