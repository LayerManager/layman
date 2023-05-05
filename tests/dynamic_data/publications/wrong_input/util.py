import inspect
import itertools

from tests import Publication
from tests.dynamic_data import base_test_classes


def case_to_simple_parametrizations(case):
    result = set()
    if case is not None:
        dimensions_values = []
        for item in case:
            if inspect.isclass(item) \
                    and (issubclass(item, base_test_classes.RestArgDomain)
                         or issubclass(item, base_test_classes.RestMethod)
                         or issubclass(item, base_test_classes.PublicationByDefinitionBase)):
                dimensions_values.append(list(item))
            else:
                dimensions_values.append([item])
        for parametrization in itertools.product(*dimensions_values):
            parametrization = frozenset(parametrization)
            assert parametrization not in result
            result.add(parametrization)
    return result


def format_exception(exception_info: dict, publication: Publication):
    format_variables = {
        'publication_name': publication.name,
        'workspace': publication.workspace,
    }
    if 'data' in exception_info and isinstance(exception_info['data'], dict):
        if 'path' in exception_info['data']:
            exception_info['data']['path'] = exception_info['data']['path'].format(**format_variables)
        if 'file' in exception_info['data']:
            exception_info['data']['file'] = exception_info['data']['file'].format(**format_variables)
        if 'files' in exception_info['data']:
            exception_info['data']['files'] = [file.format(**format_variables) for file in exception_info['data']['files']]
        if 'unmatched_filenames' in exception_info['data']:
            exception_info['data']['unmatched_filenames'] = [file.format(**format_variables) for file in exception_info['data']['unmatched_filenames']]
        if 'too_long_filenames' in exception_info['data']:
            exception_info['data']['too_long_filenames'] = [file.format(**format_variables) for file in exception_info['data']['too_long_filenames']]
        if 'similar_filenames_mapping' in exception_info['data']:
            exception_info['data']['similar_filenames_mapping'] = {key.format(**format_variables): value.format(**format_variables) for
                                                                   key, value in exception_info['data']['similar_filenames_mapping'].items()}
