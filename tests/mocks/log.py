from .base import fake, BaseGenerator
from api.models import Log, LogValue, ValueTypeEnum, Parameter, ApplianceParameter, Appliance


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
                           **kwargs):
        if not value_mapper:
            value_mapper = {}

        log_values = []
        log_model = Log(appliance_id=appliance.id,
                        organisation_id=appliance.organisation_id)
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
            else:
                value = value_mapper.get(param.id,
                                         'This is just a comment log')
            log_values.append(
                LogValue(log_id=log_model.id,
                         parameter_id=param.id,
                         value=value))
        log_values = LogValue.bulk_create(log_values, commit=save)
        return log_model, log_values
