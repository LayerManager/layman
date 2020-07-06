from celery import Celery, signals
from celery.contrib import abortable
from layman import settings
from .util import get_modules_from_names


def make_celery(app):
    celery_app = Celery(
        'layman',
        backend=settings.LAYMAN_REDIS_URL,
        broker=settings.LAYMAN_REDIS_URL,
        include=get_task_modules(),
    )
    celery_app.conf.update(
        # http://docs.celeryproject.org/en/latest/getting-started/brokers/redis.html
        broker_transport_options={
            'visibility_timeout': 3600,  # 1 hour
            'fanout_prefix': True,
            'fanout_patterns': True,
        },
        # https://stackoverflow.com/a/38267978
        task_track_started=True,
    )

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


@signals.task_prerun.connect
def on_task_prerun(**kwargs):
    task_name = kwargs['task'].name
    from layman import app, celery_app
    from layman.util import get_publication_types
    from layman.celery import task_prerun
    with app.app_context():
        publication_type = next(
            (
                v for k, v in get_publication_types().items()
                if task_name.startswith(k)
            ),
            None
        )
        if publication_type is None:
            return
        username = kwargs['args'][0]
        publication_name = kwargs['args'][1]
        task_id = kwargs['task_id']
        task_prerun(username, publication_type, publication_name, task_id, task_name)


@signals.task_postrun.connect
def on_task_postrun(**kwargs):
    task_name = kwargs['task'].name
    from layman import app, celery_app
    from layman.util import get_publication_types
    from layman.celery import task_postrun
    with app.app_context():
        publication_type = next(
            (
                v for k, v in get_publication_types().items()
                if task_name.startswith(k)
            ),
            None
        )
        if publication_type is None:
            return
        username = kwargs['args'][0]
        publication_name = kwargs['args'][1]
        task_id = kwargs['task_id']
        task_postrun(username, publication_type, publication_name, task_id, task_name, kwargs['state'])
