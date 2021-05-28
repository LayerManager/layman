import importlib
import inspect
from celery import chain

from layman import settings


def get_task_chain(publ_type, workspace, publ_name, task_options, start_at, publ_param_name):
    methods = get_task_methods(publ_type, workspace, publ_name, task_options, start_at)
    return get_chain_of_methods(workspace, publ_name, methods, task_options, publ_param_name)


def get_task_methods(publ_type, workspace, publ_name, task_options, start_at):
    if start_at is None:
        return []
    internal_sources = list(publ_type['internal_sources'].keys())
    start_idx = internal_sources.index(start_at)
    source_names = [
        m for m in internal_sources[start_idx:]
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
        if needed_method(workspace, publ_name, task_options):
            task_methods.append(task_method)
    return task_methods


def get_source_task_methods(publ_type, method_name):
    source_module_names = list(publ_type['internal_sources'].keys())
    task_module_names = [f"{name}_tasks" for name in source_module_names]
    task_methods = []
    for task_module_name in task_module_names:
        try:
            task_module = importlib.import_module(task_module_name)
        except ModuleNotFoundError:
            continue
        task_method = getattr(task_module, method_name, None)
        if task_method is None:
            continue
        task_methods.append(task_method)
    return task_methods


def get_chain_of_methods(workspace, publ_name, task_methods, task_options, publ_param_name):
    return chain(*[
        get_task_signature(workspace, publ_name, t, task_options, publ_param_name)
        for t in task_methods
    ])


def get_task_signature(workspace, publ_name, task, task_options, publ_param_name):
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
        (workspace, publ_name),
        task_opts,
        queue=settings.LAYMAN_CELERY_QUEUE,
        immutable=True,
    )
