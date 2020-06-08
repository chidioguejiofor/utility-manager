from api.utils.exceptions import ResponseException
from api.utils.error_messages import serialization_error
from .base import BaseOrgView, BasePaginatedView, BaseValidateRelatedOrgModelMixin
from settings import org_endpoint
from flask import request
from api.models import Parameter, ApplianceParameter, ApplianceCategory, Appliance
from api.schemas import ApplianceSchema, ApplianceParameterSchema
from api.utils.success_messages import RETRIEVED, CREATED


@org_endpoint('/formulas')
class FormulaView(BaseOrgView, BasePaginatedView,
                  BaseValidateRelatedOrgModelMixin):
    __model__ = Appliance
    __SCHEMA__ = ApplianceSchema
    PROTECTED_METHODS = ['POST', 'GET']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    # FILTER_QUERY_MAPPER = {
    #     'category_id': 'appliance_category_id',
    #     'category_name': 'appliance_category.name',
    # }
    # query settings
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': '-name,created_at',
        'sort_fields': {'created_at', 'name', 'category_id'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Appliances')

    VALIDATE_RELATED_KWARGS = {
        # "parameter_ids": {
        #     'model':
        #     Parameter,
        #     'err_message':
        #     serialization_error['not_found'].format('Some parameters')
        # },
        # "categoryId": {
        #     "model":
        #     ApplianceCategory,
        #     'err_message':
        #     serialization_error['not_found'].format('Appliance Category')
        # },
    }

    # EAGER_LOADING_FIELDS = ['appliance_category']

    def post(self, org_id, user_data, membership):
        pass
