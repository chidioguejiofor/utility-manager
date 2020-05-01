from api.utils.exceptions import ResponseException
from api.utils.error_messages import serialization_error
from .base import BaseOrgView, BasePaginatedView
from settings import org_endpoint
from flask import request
from api.models import Parameter, ApplianceParameter, ApplianceCategory, Appliance
from api.schemas import ApplianceSchema
from api.schemas import LogSchema, ParameterSchema
from api.utils.success_messages import SAVED, RETRIEVED, CREATED


@org_endpoint('/appliance-category/<string:category_id>/appliances')
class ApplianceView(BaseOrgView, BasePaginatedView):
    __model__ = Appliance
    __SCHEMA__ = ApplianceSchema
    PROTECTED_METHODS = ['POST', 'GET']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    # query settings
    SEARCH_FILTER_ARGS = {
        'label': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {'defaults': 'created_at', 'sort_fields': {'created_at'}}

    def filter_get_method_query(self, query, *args, org_id, **kwargs):
        return query.filter(
            self.__model__.appliance_category_id == kwargs['category_id'])

    def post(self, org_id, category_id, user_data, membership):
        json_data = request.get_json()
        json_data = json_data if json_data else {}
        json_data['organisationId'] = org_id
        json_data['created_by_id'] = user_data['id']
        json_data['appliance_category_id'] = category_id
        validated_data = ApplianceSchema().load(json_data)

        cat_count = ApplianceCategory.query.filter_by(
            id=category_id,
            organisation_id=org_id,
        ).count()
        if cat_count == 0:
            raise ResponseException(
                message=serialization_error['not_found'].format(
                    'Appliance Category'),
                status_code=404,
            )
        params = set(validated_data['parameters'])
        valid_parameters = Parameter.query.filter(
            Parameter.id.in_(params)).count()
        invalid_parameter_count = len(params) - valid_parameters

        if invalid_parameter_count > 0:
            raise ResponseException(
                message=serialization_error['some_ids_not_found'].format(
                    f'{invalid_parameter_count} parameters'))

        appliance_obj = Appliance(
            label=validated_data['label'],
            specs=validated_data['specs'],
            appliance_category_id=category_id,
            organisation_id=org_id,
            created_by_id=user_data['id'],
        )

        appliance_obj.save()

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
