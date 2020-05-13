from api.utils.id_generator import IDGenerator
from .base import fake, BaseGenerator
from api.models import Appliance, ApplianceParameter
from api.utils.helper_functions import capitalize_each_word_in_sentence


class ApplianceGenerator(BaseGenerator):
    __model__ = Appliance

    @classmethod
    def generate_api_input_data(cls, parameters, category_id=''):
        return {
            'categoryId': category_id,
            'label':
            capitalize_each_word_in_sentence(fake.name()[:30].strip()),
            'specs': {
                'powerRating': 4000,
                'serialNumber': 'N-20110-888',
            },
            'parameters': parameters
        }

    @classmethod
    def generate_model_obj_dict(cls, org_id, parameters, **kwargs):
        appliance_id = IDGenerator.generate_id()
        appliance_parameters = [{
            'appliance_id': appliance_id,
            'parameter_id': parameter.id
        } for parameter in parameters]
        appliance_obj = cls.generate_api_input_data(parameters)
        del appliance_obj['parameters']
        del appliance_obj['categoryId']
        return {
            'id': appliance_id,
            'organisation_id': org_id,
            **appliance_obj,
            **kwargs
        }, appliance_parameters

    @classmethod
    def generate_model_obj(cls, *args, save=False, **kwargs):
        appliance, appliance_parameters = cls.generate_model_obj_dict(
            *args, **kwargs)
        appliance_model = Appliance(**appliance)
        appliance_model.save(commit=save)
        appliance_parameters_model = ApplianceParameter.bulk_create(
            appliance_parameters, commit=save)
        return appliance_model, appliance_parameters_model
