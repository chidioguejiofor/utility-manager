from api.utils.exceptions import ResponseException
from api.utils.error_messages import serialization_error
from .base import BaseOrgView, BasePaginatedView
from settings import org_endpoint
from flask import request
from api.models import ValueTypeEnum, Log, LogValue, Parameter
from api.schemas import LogSchema
from api.utils.success_messages import SAVED, RETRIEVED


@org_endpoint('/logs')
class LogsView(BaseOrgView, BasePaginatedView):
    __SCHEMA__ = LogSchema
    __model__ = Log
    PROTECTED_METHODS = ['POST', 'GET']
    ALLOWED_ROLES = {
        'POST': ['OWNER', 'ADMIN', 'ENGINEER'],
        'GET': ['OWNER', 'ADMIN', 'ENGINEER'],
    }

    SORT_KWARGS = {
        'defaults': '-created_at, -updated_at',
        'sort_fields': {'created_at', 'updated_at'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Logs')
    EAGER_LOADING_FIELDS = ['log_values']
    SEARCH_FILTER_ARGS = {
        'appliance_id': {
            'filter_type': 'eq'
        },
    }

    # SCHEMA_EXCLUDE = ['appliance_id']

    def filter_get_method_query(self, query, *args, **kwargs):
        return query.filter_by(organisation_id=kwargs.get('org_id'))

    def post(self, org_id, user_data, membership, **kwargs):
        request_dict = LogSchema().load(request.get_json())
        appliance_id = request_dict['appliance_id']
        log_data = request_dict['log_data']
        param_objs = Parameter.get_parameters_in_appliance(
            org_id, appliance_id).all()

        error_objs = {}

        if len(param_objs) == 0:
            raise ResponseException(
                message=serialization_error['not_found'].format('Appliance'), )
        log_model = Log(organisation_id=org_id,
                        appliance_id=appliance_id,
                        created_by_id=user_data['id'])
        log_model.save(commit=False)
        log_values = []
        for param in param_objs:
            request_value = log_data.get(param.id)
            if request_value is None:
                error_objs[param.id] = serialization_error['required']
            elif (param.value_type == ValueTypeEnum.NUMERIC
                  and self.validate_numeric_value(request_value) is False):
                error_objs[param.id] = serialization_error['number_only']
            else:
                log_values.append(
                    LogValue(value=request_value,
                             parameter_id=param.id,
                             log_id=log_model.id))

        if error_objs:
            raise ResponseException(
                message=serialization_error['invalid_field_data'],
                status_code=400,
                errors=error_objs)

        LogValue.bulk_create(log_values, commit=True)

        saved_log_model = Log.eager('log_values').filter_by(
            id=log_model.id).first()
        return LogSchema().dump_success_data(saved_log_model,
                                             SAVED.format('Log')), 201

    @staticmethod
    def validate_numeric_value(num_with_str):
        try:
            return float(num_with_str)
        except ValueError:
            return False
