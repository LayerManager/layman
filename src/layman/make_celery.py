import importlib.util
from celery import Celery, signals
from celery.contrib import abortable
from layman import settings
from .util import get_modules_from_names


# pylint: disable=too-few-public-methods
# pylint: disable=abstract-method
def make_celery(app):
    celery_app = Celery(
        'layman',
        backend=settings.LAYMAN_REDIS_URL,
        broker=settings.LAYMAN_REDIS_URL,
        include=get_task_modules(),
    )
    celery_app.conf.update(
        # https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html
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
            for internal_source_name in type_def['internal_sources']:
                tasks_module_name = internal_source_name + "_tasks"
                if importlib.util.find_spec(tasks_module_name) is not None:
                    task_modules.append(tasks_module_name)
    return task_modules


@signals.task_prerun.connect
def on_task_prerun(**kwargs):
    task_name = kwargs['task'].name
    from layman import app
    from layman.util import get_publication_types
    from layman.celery import task_prerun
    with app.app_context():
        publication_type = next(
            (
                v['type'] for k, v in get_publication_types().items()
                if task_name.startswith(k)
            ),
            None
        )
        if publication_type is None:
            return
        workspace = kwargs['args'][0]
        publication_name = kwargs['args'][1]
        task_id = kwargs['task_id']
        task_prerun(workspace, publication_type, publication_name, task_id, task_name)


@signals.task_postrun.connect
def on_task_postrun(**kwargs):
    task_name = kwargs['task'].name
    from layman import app
    from layman.util import get_publication_types
    from layman.celery import task_postrun
    with app.app_context():
        publication_type = next(
            (
                v['type'] for k, v in get_publication_types().items()
                if task_name.startswith(k)
            ),
            None
        )
        if publication_type is None:
            return
        workspace = kwargs['args'][0]
        publication_name = kwargs['args'][1]
        task_id = kwargs['task_id']
        task_postrun(workspace, publication_type, publication_name, task_id, task_name, kwargs['state'])
