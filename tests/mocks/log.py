from .base import fake, BaseGenerator
from api.models import Log, LogValue, ValueTypeEnum, Parameter, ApplianceParameter, Appliance
from datetime import datetime


class LogGenerator(BaseGenerator):
    @classmethod
    def generate_api_input_data(cls):
        return {}

    @classmethod
    def generate_model_obj(cls,
                           appliance,
                           save=True,
                           value_mapper=None,
                           parameters=None,
                           log_date_time=None,
                           **kwargs):
        log_date_time = datetime.now() if not log_date_time else log_date_time
        if not value_mapper:
            value_mapper = {}

        log_values = []
        log_model = Log(
            appliance_id=appliance.id,
            organisation_id=appliance.organisation_id,
            created_at=log_date_time,
        )
        log_model.save(commit=False)
        if not parameters:
            parameters = Parameter.query.join(
                ApplianceParameter,
                ApplianceParameter.parameter_id == Parameter.id).join(
                    Appliance,
                    (ApplianceParameter.appliance_id == Appliance.id) &
                    (Appliance.id == appliance.id)).all()

        for index, param in enumerate(parameters):

            if param.value_type == ValueTypeEnum.NUMERIC:
                value = value_mapper.get(param.id, index * 50)
                type_key = 'numeric_value'
            else:
                value = value_mapper.get(param.id,
                                         'This is just a comment log')
            value_key = f'{param.value_type.name.lower()}_value'
            value_kwargs = {value_key: value}
            log_values.append(
                LogValue(log_id=log_model.id,
                         parameter_id=param.id,
                         **value_kwargs))
        log_values = LogValue.bulk_create(log_values, commit=save)
        return log_model, log_values
