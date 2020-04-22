from api.utils.exceptions import ResponseException
from flask import request
from .base import BaseOrgView
from api.models import Parameter, ApplianceParameter, Appliance, db, ValueTypeEnum, Log, LogValue
from api.schemas import LogSchema
from settings import org_endpoint
from api.utils.error_messages import serialization_error


@org_endpoint('/appliances/<string:appliance_id>/logs')
class LogsView(BaseOrgView):
    PROTECTED_METHODS = ['POST']

    def post(self, org_id, user_data, membership, appliance_id, **kwargs):
        request_dict = request.get_json()

        param_test = (ApplianceParameter.parameter_id == Parameter.id) & (
            Parameter.organisation_id == org_id)
        appliance_test = ((ApplianceParameter.appliance_id == Appliance.id) &
                          (Appliance.id == appliance_id) &
                          (Appliance.organisation_id == org_id))

        param_objs = db.session.query(Parameter).join(
            ApplianceParameter,
            param_test,
        ).join(Appliance, appliance_test).all()

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
            request_value = request_dict.get(param.id)
            if not request_value:
                error_objs[param.id] = serialization_error['required']
            elif param.value_type == ValueTypeEnum.NUMERIC and self.validate_numeric_value(
                    request_value) is False:
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
        return LogSchema().dump_success_data(saved_log_model)

    @staticmethod
    def validate_numeric_value(num_with_str):
        try:
            return float(num_with_str)
        except ValueError:
            return False
