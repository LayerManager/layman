import pytest

from test_tools import process_client
from test_tools.external_db import URI_STR
from tests import EnumTestTypes, PublicationValues
from tests.dynamic_data.publications import common_publications
from .base_test_classes import RestMethod, RestArgs, CompressDomain, PublicationByUsedServers, LayerByUsedServers, CompressDomainBase, TestCaseType, Parametrization, WithChunksDomain, StyleFileDomainBase, PublicationByDefinitionBase
from . import base_test_util as util


@pytest.mark.parametrize('dimension, exp_output', [
    (RestMethod, RestMethod),
    (RestArgs.COMPRESS, CompressDomain),
    (CompressDomain, CompressDomain),
    (PublicationByUsedServers, PublicationByUsedServers),
])
def test_get_dimension_enum(dimension, exp_output):
    assert util.get_dimension_enum(dimension) == exp_output


class WrongCustomCompressDomain(CompressDomainBase):
    FALSE = (False, None)
    TRUE = ('abc', 'zipped')


class CustomCompressDomain(CompressDomainBase):
    FALSE = (False, None)
    TRUE = (True, 'compressed')


class CustomCompressDomainWithCompressSettings(CompressDomainBase):
    FALSE = (False, None)
    TRUE = (True, 'zipped', {
        'compress_settings': process_client.CompressTypeDef(archive_name='data_zip'),
    })


class PublicationByCompress(PublicationByDefinitionBase):
    LAYER = (common_publications.SMALL_LAYER, '')
    LAYER_COMPRESS = (common_publications.SMALL_LAYER_ZIP, 'zipped')


class PublicationByCompressSettings(PublicationByDefinitionBase):
    LAYER = (PublicationValues(
        type=process_client.LAYER_TYPE,
        definition={},
        info_values={},
        thumbnail='',
        legend_image='',
    ), 'no_compress_settings')
    LAYER_COMPRESS_SETTINGS = (PublicationValues(
        type=process_client.LAYER_TYPE,
        definition={
            'compress_settings': process_client.CompressTypeDef(archive_name='data_zip')
        },
        info_values={},
        thumbnail='',
        legend_image='',
    ), 'compress_settings')


class PublicationByInputData(PublicationByDefinitionBase):
    FILE = (PublicationValues(
        type=process_client.LAYER_TYPE,
        definition={
            'file_paths': ['sample/layman.layer/small_layer.geojson'],
        },
        info_values={},
        thumbnail='',
        legend_image='',
    ), 'file')
    EXTERNAL_TABLE = (PublicationValues(
        type=process_client.LAYER_TYPE,
        definition={
            'db_connection': URI_STR,
        },
        info_values={},
        thumbnail='',
        legend_image='',
    ), 'external_table')


class CustomStyleFileDomain(StyleFileDomainBase):
    SLD = ((None, 'sld'), 'sld')
    QML = (('sample/style/small_layer.qml', 'qml'), 'qml')


ONLY_DIMENSIONS_MSG = f"Only dimensions are allowed in cls.rest_parametrization. Dimension is " \
                      f"(a) instance of RestMethod, " \
                      f"(b) instance of base_domain of any RestArgs item, or " \
                      f"(c) instance of PublicationByDefinitionBase."


@pytest.mark.parametrize('rest_parametrization, exp_message', [
    pytest.param({}, "rest_parametrization must be list. Found: <class 'dict'>", id='empty-dict'),
    pytest.param(set(), "rest_parametrization must be list. Found: <class 'set'>", id='empty-set'),
    pytest.param([RestArgs.COMPRESS, RestArgs.COMPRESS], 'RestArgs.compress dimension can be used only once in parametrization',
                 id='duplicate-arg-dimension1'),
    pytest.param([RestArgs.COMPRESS, CompressDomain], 'RestArgs.compress dimension can be used only once in parametrization',
                 id='duplicate-arg-dimension2'),
    pytest.param([RestArgs.COMPRESS, CustomCompressDomain], 'RestArgs.compress dimension can be used only once in parametrization',
                 id='duplicate-arg-dimension3'),
    pytest.param([CompressDomain, CustomCompressDomain], 'RestArgs.compress dimension can be used only once in parametrization',
                 id='duplicate-arg-dimension4'),
    pytest.param([PublicationByUsedServers, LayerByUsedServers], 'PublicationByDefinitionBase dimension can be used only once in parametrization',
                 id='duplicate-publication-definition-dimension'),
    pytest.param([RestArgs.COMPRESS, PublicationByCompress], 'Rest argument compress can be used only once in parametrization. Found in two dimensions: RestArgs.COMPRESS and PublicationByCompress.LAYER_COMPRESS',
                 id='duplicate-rest-arg-and-publication-definition'),
    pytest.param([CustomCompressDomainWithCompressSettings, PublicationByCompressSettings],
                 'Rest argument compress_settings can be used only once in parametrization. Found in two dimensions: CustomCompressDomainWithCompressSettings.TRUE (in other_rest_args) and PublicationByCompressSettings.LAYER_COMPRESS_SETTINGS',
                 id='duplicate-other-rest-arg-and-publication-definition'),
    pytest.param(['a'], f"{ONLY_DIMENSIONS_MSG} Found: a", id='string'),
    pytest.param([[1, 2]], f"{ONLY_DIMENSIONS_MSG} Found: [1, 2]",
                 id='list-of-numbers'),
    pytest.param([RestArgs], f"{ONLY_DIMENSIONS_MSG} Found: <enum 'RestArgs'>",
                 id='rest-args'),
    pytest.param([WrongCustomCompressDomain], 'Values {False, \'abc\'} is not subset of values of base argument {False, True}, base_arg=RestArgs.COMPRESS.',
                 id='wrong-custom-domain'),
    pytest.param([StyleFileDomainBase], 'Dimension at idx 0 has no value.', id='one-dimension-without-value'),
    pytest.param([RestArgs.WITH_CHUNKS, CompressDomainBase], 'Dimension at idx 1 has no value.',
                 id='one-dimension-without-value-at-idx-1'),
])
def test_check_rest_parametrization_raises(rest_parametrization, exp_message):
    with pytest.raises(AssertionError) as exc_info:
        util.check_rest_parametrization(rest_parametrization)
    assert str(exc_info.value) == exp_message


@pytest.mark.parametrize('rest_parametrization', [
    pytest.param([], id='empty-list'),
    pytest.param([RestMethod], id='rest-method'),
    pytest.param([RestArgs.COMPRESS], id='rest-args-compress'),
    pytest.param([CompressDomain], id='compress-domain'),
    pytest.param([RestArgs.COMPRESS, RestArgs.WITH_CHUNKS], id='two-rest-args'),
    pytest.param([RestMethod, RestArgs.COMPRESS, RestArgs.WITH_CHUNKS], id='rest-method-and-args'),
    pytest.param([RestMethod, PublicationByUsedServers], id='rest-method-and-publication-by-definition'),
    pytest.param([CustomStyleFileDomain], id='custom-style-file'),
    pytest.param([PublicationByInputData, CustomStyleFileDomain], id='publication-by-definition-and-rest-arg'),
])
def test_check_rest_parametrization_passes(rest_parametrization):
    util.check_rest_parametrization(rest_parametrization)


@pytest.mark.parametrize('test_cases, rest_parametrization, exp_message', [
    pytest.param([TestCaseType(key='case1',
                               parametrization=Parametrization([CompressDomain.TRUE]))],
                 [CompressDomain],
                 'Attribute parametrization is meant only for output test cases, test_case=case1',
                 id='with-parametrization'),
    pytest.param([TestCaseType(key='case1',
                               type=EnumTestTypes.MANDATORY,
                               specific_types={frozenset([CompressDomain.TRUE]): EnumTestTypes.MANDATORY})],
                 [CompressDomain],
                 'No need to set specific test type that is same as main type: specific_typeEnumTestTypes.MANDATORY, type=EnumTestTypes.MANDATORY test_case=case1',
                 id='repeated-type'),
    pytest.param([TestCaseType(key='case1',
                               specific_types={frozenset([CompressDomain.TRUE]): EnumTestTypes.MANDATORY})],
                 [CompressDomain, RestMethod],
                 'Specific parametrization must have same number of members as rest_paramertization, test_case=case1, attribute=specific_types, idx=0',
                 id='wrong-specific-parametrization'),
    pytest.param([TestCaseType(key='case1',
                               rest_args={'compress': True})],
                 [CompressDomain],
                 'REST argument can be set either in parametrization or in test case, not both: RestArgs.COMPRESS, test_case=case1',
                 id='conflict-rest_args-and-parametrization'),
    pytest.param([TestCaseType(key='case1',
                               rest_args={'compress': True})],
                 [PublicationByCompress],
                 'REST argument can be set either in parametrization or in test case, not both: compress, test_case=case1',
                 id='conflict-rest_args-and-publication-definition'),
    pytest.param([TestCaseType(key='case1',
                               rest_args={'compress_settings': None})],
                 [CustomCompressDomainWithCompressSettings],
                 'REST argument can be set either in parametrization or in test case, not both: compress_settings (in CustomCompressDomainWithCompressSettings.TRUE.other_rest_args), test_case=case1',
                 id='conflict-rest_args-and-other_rest_args'),
])
def test_check_input_test_cases_raises(test_cases, rest_parametrization, exp_message):
    util.check_rest_parametrization(rest_parametrization)
    parametrizations = util.rest_parametrization_to_parametrizations(rest_parametrization)

    with pytest.raises(AssertionError) as exc_info:
        util.check_input_test_cases(test_cases, rest_parametrization, parametrizations)
    assert str(exc_info.value) == exp_message


@pytest.mark.parametrize('rest_parametrization, specific_parametrizations, attribute_name, exp_message', [
    pytest.param([RestArgs.COMPRESS, RestArgs.WITH_CHUNKS],
                 [frozenset([CompressDomain.TRUE])],
                 'specific_params',
                 'Specific parametrization must have same number of members as rest_paramertization, test_case=case1, attribute=specific_params, idx=0',
                 id='different-length'),
    pytest.param([RestArgs.COMPRESS, RestArgs.WITH_CHUNKS],
                 [frozenset([CompressDomain.TRUE, PublicationByUsedServers.LAYER_RASTER])],
                 'specific_types',
                 'Specific parametrization must have exactly one value of dimension RestArgs.WITH_CHUNKS. Found 0 values. test_case=case1, attribute=specific_types, idx=0',
                 id='missing-dimension-value'),
    pytest.param([RestArgs.COMPRESS, RestArgs.WITH_CHUNKS],
                 [frozenset([CompressDomain.TRUE, CompressDomain.FALSE])],
                 'specific_types',
                 'Specific parametrization must have exactly one value of dimension RestArgs.COMPRESS. Found 2 values. test_case=case1, attribute=specific_types, idx=0',
                 id='two-values-of-the-same-dimension'),
])
def test_check_specific_parametrizations_raises(rest_parametrization, specific_parametrizations, attribute_name, exp_message):
    util.check_rest_parametrization(rest_parametrization)

    with pytest.raises(AssertionError) as exc_info:
        util.check_specific_parametrizations(rest_parametrization, specific_parametrizations, test_case_key='case1',
                                             attribute_name=attribute_name)
    assert str(exc_info.value) == exp_message


@pytest.mark.parametrize('rest_parametrization, exp_output', [
    pytest.param([], [Parametrization([])], id='empty'),
    pytest.param([RestMethod], [Parametrization([RestMethod.POST]), Parametrization([RestMethod.PATCH])],
                 id='one-dimension'),
    pytest.param([RestMethod, RestArgs.COMPRESS], [Parametrization([RestMethod.POST, CompressDomain.FALSE]),
                                                   Parametrization([RestMethod.POST, CompressDomain.TRUE]),
                                                   Parametrization([RestMethod.PATCH, CompressDomain.FALSE]),
                                                   Parametrization([RestMethod.PATCH, CompressDomain.TRUE]),
                                                   ],
                 id='two-dimensions'),
    pytest.param([RestMethod, CustomCompressDomain], [Parametrization([RestMethod.POST, CustomCompressDomain.FALSE]),
                                                      Parametrization([RestMethod.POST, CustomCompressDomain.TRUE]),
                                                      Parametrization([RestMethod.PATCH, CustomCompressDomain.FALSE]),
                                                      Parametrization([RestMethod.PATCH, CustomCompressDomain.TRUE]),
                                                      ],
                 id='two-dimensions-one-custom'),
    pytest.param([CustomStyleFileDomain], [Parametrization([CustomStyleFileDomain.SLD]),
                                           Parametrization([CustomStyleFileDomain.QML]),
                                           ],
                 id='one-custom-rest-arg-whose-parent-is-without-domain'),
])
def test_rest_parametrization_to_parametrizations(rest_parametrization, exp_output):
    util.check_rest_parametrization(rest_parametrization)

    assert util.rest_parametrization_to_parametrizations(rest_parametrization) == exp_output


@pytest.mark.parametrize('parametrization, exp_props', [
    pytest.param(Parametrization([]), {
        'values_list': [],
        'values_set': frozenset([]),
        'publication_definition': None,
        'rest_method': None,
        'rest_arg_dict': {},
    }, id='empty-list'),
    pytest.param(Parametrization([CompressDomain.TRUE, WithChunksDomain.FALSE]), {
        'values_list': [CompressDomain.TRUE, WithChunksDomain.FALSE],
        'values_set': frozenset([CompressDomain.TRUE, WithChunksDomain.FALSE]),
        'publication_definition': None,
        'rest_method': None,
        'rest_arg_dict': {
            RestArgs.COMPRESS: CompressDomain.TRUE,
            RestArgs.WITH_CHUNKS: WithChunksDomain.FALSE,
        },
    }, id='two-rest-args'),
    pytest.param(Parametrization([RestMethod.PATCH, CompressDomain.TRUE, WithChunksDomain.FALSE]), {
        'publication_definition': None,
        'rest_method': RestMethod.PATCH,
        'rest_arg_dict': {
            RestArgs.COMPRESS: CompressDomain.TRUE,
            RestArgs.WITH_CHUNKS: WithChunksDomain.FALSE,
        },
    }, id='rest-method-and-two-rest-args'),
    pytest.param(Parametrization([RestMethod.PATCH, PublicationByUsedServers.LAYER_RASTER]), {
        'publication_definition': PublicationByUsedServers.LAYER_RASTER.publication_definition,
        'rest_method': RestMethod.PATCH,
        'rest_arg_dict': {},
    }, id='rest-method-and-publication-definition'),
])
def test_parametrization_class_props(parametrization, exp_props):
    for prop_name, prop_value in exp_props.items():
        assert getattr(parametrization, prop_name) == prop_value, f"prop_name={prop_name}"
