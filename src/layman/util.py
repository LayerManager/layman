from functools import wraps
import importlib
import copy
import inspect
import os
import pathlib
import re
import unicodedata
import urllib.parse
from collections import OrderedDict
import logging

from flask import current_app, request, jsonify
from unidecode import unidecode

from layman import settings, celery as celery_util, common
from layman.common import tasks as tasks_util, redis
from layman.http import LaymanError

logger = logging.getLogger(__name__)

WORKSPACE_NAME_ONLY_PATTERN = r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*"

WORKSPACE_NAME_PATTERN = r"^" + WORKSPACE_NAME_ONLY_PATTERN + r"$"

FLASK_PROVIDERS_KEY = f'{__name__}:PROVIDERS'
FLASK_PUBLICATION_TYPES_KEY = f'{__name__}:PUBLICATION_TYPES'
FLASK_PUBLICATION_MODULES_KEY = f'{__name__}:PUBLICATION_MODULES'


class SimpleStorage:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class SimpleCounter:
    def __init__(self):
        self.counter = 0

    def increase(self):
        self.counter += 1

    def decrease(self):
        self.counter -= 1

    def get(self):
        return self.counter


def slugify(value):
    value = unidecode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s\-\.]', '', value).lower()
    value = re.sub(r'[\s\-\._]+', '_', value).strip('_')
    return value


def to_safe_name(unsafe_name, type_name):
    value = slugify(unsafe_name)
    if len(value) == 0:
        value = type_name
    elif re.match(r'^[^0-9a-z].*', value):
        value = f'{type_name}_{value}'
    return value


def to_safe_names(unsafe_names, type_name):
    values = [slugify(n) for n in unsafe_names]
    values = [v for v in values if len(v) > 0]
    values_letter_prefix, values_other_prefix = [], []
    for value in values:
        (values_other_prefix if re.match(r'^[^a-z].*', value) else values_letter_prefix).append(value)
    values = values_letter_prefix + [f'{type_name}_{v}' for v in values_other_prefix]
    if len(values) == 0:
        values = [type_name]
    return values


def check_deprecated_url(response):
    regexp = rf'^/rest/{settings.REST_WORKSPACES_PREFIX}\b.*$'
    if not re.match(regexp, request.path):
        response.headers['Deprecation'] = 'version=v2'
        response.headers['Link'] = f'<{request.url.replace("/rest/",f"/rest/{settings.REST_WORKSPACES_PREFIX}/")}>; rel="alternate"'
    return response


def check_workspace_name_decorator(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        workspace = request.view_args['workspace']
        check_workspace_name(workspace, pattern_only=True)
        result = func(*args, **kwargs)
        return result

    return decorated_function


def check_reserved_workspace_names(workspace_name):
    if workspace_name in settings.RESERVED_WORKSPACE_NAMES:
        raise LaymanError(35, {'reserved_by': 'RESERVED_WORKSPACE_NAMES', 'workspace': workspace_name})


def check_workspace_name(workspace, pattern_only=False):
    if not re.match(WORKSPACE_NAME_PATTERN, workspace):
        raise LaymanError(2, {'parameter': 'workspace', 'expected': WORKSPACE_NAME_PATTERN})
    if pattern_only:
        return
    check_reserved_workspace_names(workspace)
    providers = get_internal_providers()
    call_modules_fn(providers, 'check_workspace_name', [workspace])


def get_usernames(use_cache=True, skip_modules=None):
    skip_modules = skip_modules or set()
    if use_cache:
        providers = get_internal_providers()
    else:
        all_sources = []
        for type_def in get_publication_types(use_cache=False).values():
            all_sources += type_def['internal_sources']
        providers = get_providers_from_source_names(all_sources, skip_modules)
    results = call_modules_fn(providers, 'get_usernames')
    usernames = []
    for result in results.values():
        usernames += result
    usernames = list(set(usernames))
    return usernames


def get_workspaces(use_cache=True, skip_modules=None):
    skip_modules = skip_modules or set()
    if use_cache:
        providers = get_internal_providers()
    else:
        all_sources = []
        for type_def in get_publication_types(use_cache=False).values():
            all_sources += type_def['internal_sources']
        providers = get_providers_from_source_names(all_sources, skip_modules)
    results = call_modules_fn(providers, 'get_workspaces')
    workspaces = []
    for response in results.values():
        workspaces += response
    workspaces = list(set(workspaces))
    return workspaces


def ensure_whole_user(username):
    current_app.logger.info('ensure_whole_user:' + username)
    providers = get_internal_providers()
    call_modules_fn(providers, 'ensure_whole_user', [username])


def delete_whole_user(username):
    providers = get_internal_providers()
    call_modules_fn(providers, 'delete_whole_user', [username])


def get_internal_providers():
    key = FLASK_PROVIDERS_KEY
    if key not in current_app.config:
        all_sources = []
        for type_def in get_publication_types().values():
            all_sources += type_def['internal_sources']
        current_app.config[key] = get_providers_from_source_names(all_sources)
    return current_app.config[key]


def get_publication_types(use_cache=True):
    def modules_to_types(publ_modules):
        return {
            type_name: type_def
            for publ_module in publ_modules
            for type_name, type_def in publ_module.PUBLICATION_TYPES.items()
        }
    if use_cache:
        key = FLASK_PUBLICATION_TYPES_KEY
        if key not in current_app.config:
            current_app.config[key] = modules_to_types(get_publication_modules())

        result = current_app.config[key]
    else:
        result = modules_to_types(get_publication_modules(use_cache=False))
    return result


def get_workspace_blueprints():
    blueprints = []
    for type_def in get_publication_types(use_cache=False).values():
        blueprints += type_def['workspace_blueprints']
    return blueprints


def get_blueprints():
    from .rest_publications import bp as rest_publications_bp
    blueprints = []
    for type_def in get_publication_types(use_cache=False).values():
        blueprints += type_def['blueprints']
    blueprints.append(rest_publications_bp)
    return blueprints


def get_publication_modules(use_cache=True):
    if use_cache:
        key = FLASK_PUBLICATION_MODULES_KEY
        if key not in current_app.config:
            current_app.config[key] = get_modules_from_names(settings.PUBLICATION_MODULES)
        result = current_app.config[key]
    else:
        result = get_modules_from_names(settings.PUBLICATION_MODULES)
    return result


def get_publication_module(publication_type, use_cache=True):
    modules = get_publication_modules(use_cache=use_cache)
    module = next(module for module in modules if publication_type in module.PUBLICATION_TYPES)
    return module


def get_workspace_publication_url(publication_type, workspace, publication_name, use_cache=True, *, x_forwarded_prefix=None):
    publ_module = get_publication_module(publication_type, use_cache=use_cache)
    return publ_module.get_workspace_publication_url(workspace, publication_name, x_forwarded_prefix=x_forwarded_prefix)


def get_providers_from_source_names(source_names, skip_modules=None):
    skip_modules = skip_modules or set()
    provider_names = list(OrderedDict.fromkeys(map(
        lambda src: src[:src.rfind('.')],
        source_names
    )))
    provider_names = list(set(provider_names).difference(skip_modules))
    providers = get_modules_from_names(provider_names)
    return providers


def get_modules_from_names(module_names):
    modules = [importlib.import_module(module_name) for module_name in module_names]
    return modules


def call_modules_fn(modules, fn_name, args=None, kwargs=None, omit_duplicate_calls=True, until=None):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    functions = []
    for module in modules:
        func = getattr(module, fn_name, None)
        if func is None:
            raise Exception(
                f'Module {module.__name__} does not have {fn_name} method.')
        if func not in functions or not omit_duplicate_calls:
            functions.append(func)

    results = {}
    for func in functions:
        fullargspec = inspect.getfullargspec(func)
        fn_arg_names = fullargspec[0] + fullargspec[4]  # args + kwonlyargs
        final_kwargs = {
            k: v for k, v in kwargs.items()
            if k in fn_arg_names
        }
        res = func(*args, **final_kwargs)
        results[inspect.getmodule(func)] = res
        if until is not None and until(res):
            return results

    return results


DUMB_MAP_ADAPTER_DICT = {}


def _url_for(endpoint, *, server_name, proxy_server_name, internal=False, x_forwarded_prefix=None, **values):
    assert not (internal and values.get('_external'))
    assert not (internal and x_forwarded_prefix)
    x_forwarded_prefix = x_forwarded_prefix or ''
    # It seems SERVER_NAME is not None only in some tests. It also seems TESTING is True only in the same tests.
    assert (current_app.config.get('SERVER_NAME', None) is not None) == (current_app.config['TESTING'] is True)
    # Flask does not accept SERVER_NAME without dot, and without SERVER_NAME url_for cannot be used
    # therefore DUMB_MAP_ADAPTER_DICT is created manually ...
    dict_key = f"{proxy_server_name} {x_forwarded_prefix}"
    dumb_map_adapter = DUMB_MAP_ADAPTER_DICT.get(dict_key)
    if dumb_map_adapter is None:
        dumb_map_adapter = current_app.url_map.bind(
            proxy_server_name + x_forwarded_prefix,
            url_scheme=current_app.config['PREFERRED_URL_SCHEME']
        )
        DUMB_MAP_ADAPTER_DICT[dict_key] = dumb_map_adapter
    result = dumb_map_adapter.build(endpoint, values=values, force_external=True)
    if internal:
        _, netloc, path, query, fragment = urllib.parse.urlsplit(result)
        netloc = server_name
        result = urllib.parse.urlunsplit(('http', netloc, path, query, fragment))
    return result


def url_for(endpoint, *, internal=False, x_forwarded_prefix=None, **values):
    return _url_for(endpoint, server_name=settings.LAYMAN_SERVER_NAME,
                    proxy_server_name=settings.LAYMAN_PROXY_SERVER_NAME,
                    internal=internal, x_forwarded_prefix=x_forwarded_prefix, **values)


def get_internal_sources(publ_type):
    return get_modules_from_names(get_publication_types()[publ_type]['internal_sources'])


def get_multi_info_keys_to_remove(publ_type):
    return get_publication_types()[publ_type]['multi_info_keys_to_remove']


def merge_infos(target_info, partial_info, *, comment=None):
    for key, value in partial_info.items():
        if isinstance(value, dict) and isinstance(target_info.get(key), dict):
            merge_infos(target_info[key], value, comment=comment)
        else:
            target_info[key] = value


def get_publication_info(workspace, publ_type, publ_name, context=None):
    from layman import authz
    from layman.layer import LAYER_TYPE
    from layman.map import MAP_TYPE
    context = context or {}

    assert not ('sources_filter' in context and 'keys' in context)
    sources = get_internal_sources(publ_type)
    if 'sources_filter' in context:
        sources_names = context['sources_filter'].split(',')
        if 'actor_name' in context:
            sources_names.extend([source for source, source_def in get_publication_types()[publ_type]['internal_sources'].items()
                                  if 'access_rights' in source_def.info_items])
        sources = [
            s for s in sources if s.__name__ in sources_names
        ]

    if 'keys' in context:
        keys = set(context['keys'])
        if 'actor_name' in context:
            keys.add('access_rights')
        sources_names = [source for source, source_def in get_publication_types()[publ_type]['internal_sources'].items()
                         if keys.intersection(source_def.info_items)]
        sources = [s for s in sources if s.__name__ in sources_names]
        assert sources, sources_names

    info_method = {
        LAYER_TYPE: 'get_layer_info',
        MAP_TYPE: 'get_map_info',
    }[publ_type]
    partial_infos = call_modules_fn(sources, info_method, [workspace, publ_name], kwargs={
        'extra_keys': context.get('extra_keys', []),
        'x_forwarded_prefix': context.get('x_forwarded_prefix'),
    })

    result = {}
    for source, partial_info in partial_infos.items():
        merge_infos(result, partial_info, comment=f'source={source}')

    if 'actor_name' in context and result:
        actor = context['actor_name']
        read_access_users = result.get('access_rights').get('read')
        if not authz.is_user_in_access_rule(actor, read_access_users):
            result = {}

    return result


def get_publication_infos(workspace=None, publ_type=None, context=None, style_type=None,):
    return get_publication_infos_with_metainfo(workspace=workspace, publ_type=publ_type, context=context, style_type=style_type)['items']


def get_publication_infos_with_metainfo(workspace=None, publ_type=None, context=None, style_type=None,
                                        limit=None, offset=None,
                                        full_text_filter=None,
                                        bbox_filter=None,
                                        bbox_filter_crs=None,
                                        order_by_list=None,
                                        ordering_full_text=None,
                                        ordering_bbox=None,
                                        ordering_bbox_crs=None,
                                        ):
    from layman.common.prime_db_schema import publications
    context = context or {}

    reader = (context.get('actor_name') or settings.ANONYM_USER) if context.get('access_type') == 'read' else None
    writer = (context.get('actor_name') or settings.ANONYM_USER) if context.get('access_type') == 'write' else None
    infos = publications.get_publication_infos_with_metainfo(workspace, publ_type, style_type,
                                                             reader=reader, writer=writer,
                                                             limit=limit, offset=offset,
                                                             full_text_filter=full_text_filter,
                                                             bbox_filter=bbox_filter,
                                                             bbox_filter_crs=bbox_filter_crs,
                                                             order_by_list=order_by_list,
                                                             ordering_full_text=ordering_full_text,
                                                             ordering_bbox=ordering_bbox,
                                                             ordering_bbox_crs=ordering_bbox_crs,
                                                             )

    return infos


def delete_workspace_publication(workspace, publication_type, publication):
    from layman.layer import LAYER_TYPE, util as layer_util
    from layman.map import MAP_TYPE, util as map_util

    delete_method = {
        LAYER_TYPE: layer_util.delete_layer,
        MAP_TYPE: map_util.delete_map,
    }[publication_type]

    delete_method(workspace, publication)


def delete_publications(workspace,
                        publ_type,
                        is_chain_ready_fn,
                        abort_publication_fn,
                        delete_publication_fn,
                        method,
                        url_path,
                        publ_param,
                        ):
    from layman import authn
    actor_name = authn.get_authn_username()
    whole_infos = get_publication_infos(workspace, publ_type, {'actor_name': actor_name, 'access_type': 'write'})

    for (_, _, publication) in whole_infos.keys():
        redis.create_lock(workspace, publ_type, publication, method)
        try:
            abort_publication_fn(workspace, publication)
            delete_publication_fn(workspace, publication)
            if is_chain_ready_fn(workspace, publication):
                redis.unlock_publication(workspace, publ_type, publication)
        except Exception as exc:
            try:
                if is_chain_ready_fn(workspace, publication):
                    redis.unlock_publication(workspace, publ_type, publication)
            finally:
                redis.unlock_publication(workspace, publ_type, publication)
            raise exc

    infos = [
        {
            'name': info["name"],
            'title': info.get("title", None),
            'url': url_for(**{'endpoint': url_path, publ_param: name, 'workspace': workspace}),
            'uuid': info["uuid"],
            'access_rights': info['access_rights'],
        }
        for (name, info) in whole_infos.items()
    ]
    return jsonify(infos)


def patch_after_feature_change(workspace, publication_type, publication, *, queue=None, **kwargs):
    try:
        redis.create_lock(workspace, publication_type, publication, common.PUBLICATION_LOCK_FEATURE_CHANGE)
    except LaymanError as exc:
        if exc.code == 49 and exc.private_data.get('can_run_later', False):
            celery_util.push_step_to_run_after_chain(workspace, publication_type, publication,
                                                     'layman.util::patch_after_feature_change')
            return
        raise exc
    task_methods = tasks_util.get_source_task_methods(get_publication_types()[publication_type], 'patch_after_feature_change')
    patch_chain = tasks_util.get_chain_of_methods(workspace, publication, task_methods, kwargs, 'layername', queue=queue)
    res = patch_chain()
    celery_util.set_publication_chain_info(workspace, publication_type, publication, task_methods, res)


def get_publication_status(workspace, publication_type, publication_name, complete_info, item_keys, ):
    chain_info = celery_util.get_publication_chain_info(workspace, publication_type, publication_name)
    current_lock = redis.get_publication_lock(
        workspace,
        publication_type,
        publication_name,
    )

    if (chain_info and not celery_util.is_chain_ready(chain_info)) or current_lock:
        publication_status = 'UPDATING'
    elif any(complete_info.get(v, {}).get('status') for v in item_keys if isinstance(complete_info.get(v, {}), dict)):
        publication_status = 'INCOMPLETE'
    else:
        publication_status = 'COMPLETE'
    return publication_status


def get_info_with_statuses(info, chain_info, task_to_layer_info_keys, item_keys):
    filled_info = copy.deepcopy(info)

    if chain_info is None or celery_util.is_chain_successful(chain_info):
        return filled_info

    if celery_util.is_chain_failed_without_info(chain_info):
        for res in chain_info['by_order']:
            task_name = next(k for k, v in chain_info['by_name'].items() if v == res)
            source_state = {
                'status': 'NOT_AVAILABLE'
            }
            if task_name not in task_to_layer_info_keys:
                continue
            for layerinfo_key in task_to_layer_info_keys[task_name]:
                if layerinfo_key not in filled_info:
                    filled_info[layerinfo_key] = source_state

        return filled_info

    failed = False
    for res in chain_info['by_order']:
        task_name = next(k for k, v in chain_info['by_name'].items() if v == res)
        source_state = {
            'status': res.state if not failed else 'NOT_AVAILABLE'
        }
        if res.failed() and not failed:
            failed = True
            res_exc = res.get(propagate=False)
            # current_app.logger.info(f"Exception catched: {str(res_exc)}")
            if isinstance(res_exc, LaymanError):
                source_state.update({
                    'error': res_exc.to_dict()
                })
        if task_name not in task_to_layer_info_keys:
            continue
        for layerinfo_key in task_to_layer_info_keys[task_name]:
            if layerinfo_key not in filled_info:
                if layerinfo_key in item_keys:
                    filled_info[layerinfo_key] = source_state
            elif not res.successful():
                if 'error' in source_state or 'error' not in filled_info[layerinfo_key]:
                    filled_info[layerinfo_key].update(source_state)
    return filled_info


def ensure_home_dir():
    homedir = os.environ.get('HOME')
    if (not homedir) or homedir == '/':
        homedir = '/tmp/layman_home'
        pathlib.Path(homedir).mkdir(exist_ok=True, parents=True)
        os.environ['HOME'] = homedir


def get_x_forwarded_prefix(request_headers):
    return request_headers.get('X-Forwarded-Prefix')
