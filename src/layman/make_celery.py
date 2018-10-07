from celery import Celery

def make_celery(app):
    celery_app = Celery(
        'layman',
        # app.import_name,
        backend='redis://redis:6379/0',
        broker='redis://redis:6379/0',
        include=[
            # 'layman.tasks',
            'layman.db.tasks',
        ],
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

    celery_app.Task = Task
    return celery_app