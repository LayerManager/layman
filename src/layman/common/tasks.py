from celery import chain
import importlib
import inspect
from layman import settings


def get_task_chain(publ_type, username, publ_name, task_options, start_at, publ_param_name):
    methods = get_task_methods(publ_type, username, publ_name, task_options, start_at)
    return get_chain_of_methods(username, publ_name, methods, task_options, publ_param_name)


def get_task_methods(publ_type, username, publ_name, task_options, start_at):
    if start_at is None:
        return []
    start_idx = publ_type['internal_sources'].index(start_at)
    source_names = [
        m for m in publ_type['internal_sources'][start_idx:]
        if f"{m.rsplit('.', 1)[0]}.tasks" in publ_type['task_modules']
    ]
    task_methods = []
    for source_name in source_names:
        task_module_name = f"{source_name.rsplit('.', 1)[0]}.tasks"
        task_module = importlib.import_module(task_module_name)
        method_name = f"refresh_{source_name.rsplit('.', 1)[1]}"
        task_method = getattr(task_module, method_name, None)
        if task_method is None:
            continue
        needed_method = getattr(task_module, f"{method_name}_needed")
        if needed_method(username, publ_name, task_options):
            task_methods.append(task_method)
    return task_methods


def get_chain_of_methods(username, publ_name, task_methods, task_options, publ_param_name):
    return chain(*[
        _get_task_signature(username, publ_name, t, task_options, publ_param_name)
        for t in task_methods
    ])


def _get_task_signature(username, publ_name, task, task_options, publ_param_name):
    param_names = [
        pname
        for pname in inspect.signature(task).parameters.keys()
        if pname not in ['username', publ_param_name]
    ]
    task_opts = {
        key: value
        for key, value in task_options.items()
        if key in param_names
    }
    return task.signature(
        (username, publ_name),
        task_opts,
        queue=settings.LAYMAN_CELERY_QUEUE,
        immutable=True,
    )


