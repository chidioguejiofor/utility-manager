from faker import Faker
import json
fake = Faker()


class BaseGenerator:
    __model__ = None

    @classmethod
    def generate_model_obj(cls, save=False):
        model_instance = cls.__model__(**cls.generate_model_obj_dict())
        if save:
            model_instance.save()
        return model_instance

    @classmethod
    def generate_api_input_json_data(cls):
        return json.dumps(cls.generate_api_input_data())
