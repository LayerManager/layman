from tests import Publication
from tests.dynamic_data import base_test


def format_exception(exception_info: dict, publication: Publication, parametrization: base_test.Parametrization):
    compress_value = parametrization.rest_arg_dict[base_test.RestArgs.COMPRESS].raw_value
    chunks_value = parametrization.rest_arg_dict[base_test.RestArgs.WITH_CHUNKS].raw_value
    zip_file_name = f"{publication.name}.zip" if chunks_value is True else 'temporary_zip_file.zip'
    zip_path_prefix = f"{zip_file_name}/"

    format_variables = {
        'publication_name': publication.name,
        'workspace': publication.workspace,
        'zip_file_name': zip_file_name if compress_value is True else '',
        'path_prefix': zip_path_prefix if compress_value is True else '',
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
