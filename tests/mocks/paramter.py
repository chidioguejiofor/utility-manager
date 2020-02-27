from . import fake, BaseGenerator
from api.models import Parameter, ValueTypeEnum


class ParameterGenerator(BaseGenerator):
    __model__ = Parameter

    @classmethod
    def generate_api_input_data(cls, **kwargs):
        return None

    @classmethod
    def generate_model_obj_dict(cls, **kwargs):
        return {
            'name': fake.first_name()[:30].strip(),
            'unit_id': kwargs.get('unit_id'),
            'validation': kwargs.get('validation'),
            'value_type': kwargs.get('value_type', ValueTypeEnum.NUMERIC),
            'organisation_id': kwargs.get('organisation_id'),
        }
