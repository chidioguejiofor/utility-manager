from api.utils.exceptions import ResponseException
from api.utils.error_messages import formula_errors, serialization_error
from .base import BaseOrgView, BasePaginatedView, BaseValidateRelatedOrgModelMixin
from settings import org_endpoint
from flask import request
from api.models import Formula, MathSymbolEnum, TokenTypeEnum, Unit, Parameter
from api.schemas import FormulaSchema, ApplianceParameterSchema
from api.utils.success_messages import RETRIEVED, CREATED


@org_endpoint('/formulas')
class FormulaView(BaseOrgView, BasePaginatedView,
                  BaseValidateRelatedOrgModelMixin):
    __model__ = Formula
    __SCHEMA__ = FormulaSchema
    PROTECTED_METHODS = ['POST', 'GET']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': '-name,created_at',
        'sort_fields': {'created_at', 'name'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Formula')

    formula_error_msg = 'Either some formula ids were not found or they were created with formulas'
    VALIDATE_RELATED_KWARGS = {
        "parameterId": {
            'model':
            Parameter,
            'err_message':
            serialization_error['not_found'].format(
                'Some parameter(s) you specified')
        },
        "formulaId": {
            "model": Formula,
            'err_message': formula_error_msg
        },
        "unitId": {
            "model": Unit,
            'err_message': serialization_error['not_found'].format('Unit'),
            'org_is_nullable': True,
        }
    }

    EAGER_LOADING_FIELDS = [
        'unit',
        'tokens',
        'tokens.parameter',
        'tokens.parameter.unit',
    ]

    @staticmethod
    def validate_more_model_fields(current_key, model, model_filter):
        if current_key == 'formulaId':
            return (model_filter) & (model.has_formula == False)
        return model_filter

    def post(self, org_id, user_data, membership):
        schema = FormulaSchema()
        formula_model = schema.load(request.get_json())
        formula_model.generate_id()
        parameter_ids, formula_ids = self.check_formula_token_are_valid(
            formula_model.tokens, formula_model.id)
        unit_ids = [formula_model.unit_id] if formula_model.unit_id else []
        self.validate_related_org_models(org_id,
                                         parameterId=parameter_ids,
                                         formulaId=formula_ids,
                                         unitId=unit_ids)
        formula_model.has_formula = len(formula_ids) > 0
        formula_model.organisation_id = org_id
        formula_model.save()
        return schema.dump_success_data(formula_model,
                                        CREATED.format('Formula')), 201

    @staticmethod
    def check_formula_token_are_valid(tokens, parent_id):
        bracket_stack = []
        expecting_variable = True
        parameter_id_set = set()
        formula_id_set = set()

        for index, token in enumerate(tokens):
            token.position = index
            token.parent_id = parent_id

            if token.type == TokenTypeEnum.PARAMETER:
                parameter_id_set.add(token.parameter_id)
            elif token.type == TokenTypeEnum.FORMULA:
                formula_id_set.add(token.formula_id)

            if expecting_variable and token.symbol == MathSymbolEnum.OPEN_BRACKET:
                bracket_stack.append(token)
            elif not expecting_variable and token.symbol == MathSymbolEnum.CLOSE_BRACKET:
                bracket_stack.pop()
                expecting_variable = False
            elif (expecting_variable and token.type != TokenTypeEnum.SYMBOL
                  ) or (not expecting_variable
                        and token.type == TokenTypeEnum.SYMBOL):
                expecting_variable = not expecting_variable
            else:
                raise ResponseException(
                    formula_errors['awkward_value'].format(index))
        if len(bracket_stack) > 0:
            raise ResponseException(formula_errors['missing_closing_bracket'])
        if expecting_variable:
            raise ResponseException(formula_errors['math_operation_at_end'])

        return parameter_id_set, formula_id_set
