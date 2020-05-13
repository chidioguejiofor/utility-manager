from sqlalchemy import func
from api.utils.exceptions import ResponseException
from api.utils.error_messages import serialization_error
from .base import BaseOrgView, BasePaginatedView, BaseValidateRelatedOrgModelMixin
from settings import org_endpoint
from flask import request
from api.models import Parameter, ApplianceParameter, ApplianceCategory, Appliance, Organisation
from api.schemas import ApplianceSchema
from api.schemas import ParameterSchema
from api.utils.success_messages import RETRIEVED, CREATED


@org_endpoint('/appliances')
class ApplianceView(BaseOrgView, BasePaginatedView,
                    BaseValidateRelatedOrgModelMixin):
    __model__ = Appliance
    __SCHEMA__ = ApplianceSchema
    PROTECTED_METHODS = ['POST', 'GET']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    FILTER_QUERY_MAPPER = {
        'category_id': 'appliance_category_id',
        'category_name': 'appliance_category.name',
    }
    # query settings
    SEARCH_FILTER_ARGS = {
        'label': {
            'filter_type': 'ilike'
        },
        'category_id': {
            'filter_type': 'eq'
        },
        'category_name': {
            'filter_type': 'ilike'
        }
    }

    SORT_KWARGS = {
        'defaults': 'created_at',
        'sort_fields': {'created_at', 'category_name', 'category_id'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Appliances')

    VALIDATE_RELATED_KWARGS = {
        "parameter_ids": {
            'model':
            Parameter,
            'err_message':
            serialization_error['not_found'].format('Some parameters')
        },
        "categoryId": {
            "model":
            ApplianceCategory,
            'err_message':
            serialization_error['not_found'].format('Appliance Category')
        },
    }
    EAGER_LOADING_FIELDS = ['appliance_category']

    def post(self, org_id, user_data, membership):
        json_data = request.get_json()
        json_data = json_data if json_data else {}
        json_data['organisationId'] = org_id
        json_data['created_by_id'] = user_data['id']
        validated_data = ApplianceSchema().load(json_data)
        category_id = json_data['categoryId']
        param_ids = set(validated_data['parameters'])

        self.validate_related_org_models(org_id,
                                         parameter_ids=param_ids,
                                         categoryId=[category_id])
        params = set(validated_data['parameters'])
        appliance_obj = Appliance(
            label=validated_data['label'],
            specs=validated_data['specs'],
            appliance_category_id=category_id,
            organisation_id=org_id,
            created_by_id=user_data['id'],
        )
        appliance_obj.save(commit=False)

        bulk_appliance_param = [
            ApplianceParameter(
                parameter_id=param,
                appliance_id=appliance_obj.id,
            ) for param in params
        ]

        ApplianceParameter.bulk_create(bulk_appliance_param)

        res_data = ApplianceSchema().dump_success_data(
            appliance_obj, CREATED.format('Appliance'))

        return res_data, 201


@org_endpoint('/appliances/<string:appliance_id>/parameters')
class ApplianceParamsView(BaseOrgView, BasePaginatedView):
    __SCHEMA__ = ParameterSchema
    __model__ = Parameter
    PROTECTED_METHODS = ['GET']
    ALLOWED_ROLES = {
        'GET': ['OWNER', 'ADMIN', 'ENGINEER'],
    }

    SORT_KWARGS = {
        'defaults': 'name',
        'sort_fields': {'name', 'created_at', 'updated_at'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Appliance Parameters')
    EAGER_LOADING_FIELDS = ['unit']
    SCHEMA_EXCLUDE = [
        'organisation_id', 'editable', 'updated_by', 'created_by'
    ]

    def filter_get_method_query(self, query, *args, org_id, appliance_id,
                                **kwargs):
        return Parameter.get_parameters_in_appliance(org_id, appliance_id)
