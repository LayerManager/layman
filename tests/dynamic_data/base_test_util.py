import inspect
import itertools
from collections import defaultdict
from enum import Enum
from typing import List, Iterable

from .base_test_classes import RestArgs, RestMethod, PublicationByDefinitionBase, Parametrization


def get_dimension_enum(dimension):
    return dimension if inspect.isclass(dimension) and issubclass(dimension, Enum) else dimension.domain


def check_rest_parametrization(rest_parametrization):
    assert isinstance(rest_parametrization, list), f"rest_parametrization must be list. Found: {type(rest_parametrization)}"
    rest_methods = []
    publ_by_defs = []
    base_args = defaultdict(list)

    for val_idx, val in enumerate(rest_parametrization):
        is_rest_method = val == RestMethod
        if is_rest_method:
            rest_methods.append(val)

        is_base_arg = val in list(RestArgs)
        if is_base_arg:
            base_args[val.arg_name].append(val)

        is_simple_type = is_rest_method or is_base_arg

        base_arg = inspect.isclass(val) and next((arg for arg in RestArgs if issubclass(val, arg.base_domain)), None)
        is_custom_arg_type = (not is_simple_type) and bool(base_arg)
        if is_custom_arg_type:
            base_args[base_arg.arg_name].append(val)

        is_publ_type = inspect.isclass(val) and issubclass(val, PublicationByDefinitionBase)
        if is_publ_type:
            publ_by_defs.append(val)

        assert sum([is_rest_method, is_base_arg, is_custom_arg_type, is_publ_type]) <= 1

        assert is_simple_type or is_custom_arg_type or is_publ_type, \
            f"Only dimensions are allowed in cls.rest_parametrization. Dimension is " \
            f"(a) instance of RestMethod, " \
            f"(b) instance of base_domain of any RestArgs item, or " \
            f"(c) instance of PublicationByDefinitionBase. " \
            f"Found: {val}"

        dimension_enum = get_dimension_enum(val)
        assert len(dimension_enum) > 0, f"Dimension at idx {val_idx} has no value."

        if is_custom_arg_type and base_arg.domain is not None:
            base_arg_domain_raw_values = set(v.raw_value for v in base_arg.domain)
            domain_raw_values = set(v.raw_value for v in val)
            # Expected to be changed when implementing base argument without fix enumeration, e.g. 'style'
            assert domain_raw_values <= base_arg_domain_raw_values, f"Values {domain_raw_values} is not subset of values of base argument {base_arg_domain_raw_values}, base_arg={base_arg}."

    assert len(rest_methods) <= 1, f"RestMethod dimension can be used only once in parametrization"
    assert len(publ_by_defs) <= 1, f"PublicationByDefinitionBase dimension can be used only once in parametrization"
    for arg_name, dimensions in base_args.items():
        assert len(dimensions) <= 1, f"RestArgs.{arg_name} dimension can be used only once in parametrization"

    assert len(publ_by_defs) == 0 or sum([len(dims) for dims in base_args.values()]) == 0, f"PublicationByDefinitionBase dimension must not be used with any RestArgs dimension."


def check_input_test_cases(test_cases, rest_parametrization, parametrizations: List[Parametrization]):
    is_publ_type_dimension_used = any(par for par in rest_parametrization if inspect.isclass(par) and issubclass(par, PublicationByDefinitionBase))

    for test_case in test_cases:
        assert not test_case.parametrization, f"Attribute parametrization is meant only for output test cases, test_case={test_case.key}"

        if test_case.type:
            for parametrization, specific_type in test_case.specific_types.items():
                assert specific_type != test_case.type, f"No need to set specific test type that is same as main type: specific_type{specific_type}, type={test_case.type} test_case={test_case.key}"

        for attr_name in ['specific_types', 'specific_params']:
            check_specific_parametrizations(rest_parametrization, set(getattr(test_case, attr_name)),
                                            test_case_key=test_case.key, attribute_name=attr_name)

        for parametrization in parametrizations:
            for base_arg in parametrization.rest_arg_dict:
                assert base_arg.arg_name not in test_case.rest_args, f"REST argument can be set either in parametrization or in test case, not both: {base_arg}, test_case={test_case.key}"

        if is_publ_type_dimension_used:
            assert not test_case.rest_args, f"Dimension PublicationByDefinitionBase must not be combined with rest_args, test_case={test_case.key}"


def check_specific_parametrizations(rest_parametrization, specific_parametrizations: Iterable[frozenset], *, test_case_key, attribute_name):
    for idx, sp_parametrization in enumerate(specific_parametrizations):
        # Maybe enable lower-length specific parametrizations later
        assert len(sp_parametrization) == len(rest_parametrization), f"Specific parametrization must have same number of members as rest_paramertization, test_case={test_case_key}, attribute={attribute_name}, idx={idx}"
        for dimension in rest_parametrization:
            dimension_enum = get_dimension_enum(dimension)
            param_values = [v for v in sp_parametrization if v in dimension_enum]
            assert len(param_values) == 1, f"Specific parametrization must have exactly one value of dimension {dimension}. Found {len(param_values)} values. test_case={test_case_key}, attribute={attribute_name}, idx={idx}"


def rest_parametrization_to_parametrizations(rest_parametrization):
    dimensions_values = []
    for dimension in rest_parametrization:
        all_dim_values = list(get_dimension_enum(dimension))
        dimensions_values.append(all_dim_values)

    return [Parametrization(vals) for vals in itertools.product(*dimensions_values)] or [Parametrization([])]
