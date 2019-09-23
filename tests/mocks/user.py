from . import fake, BaseGenerator
from api.models import User


class UserGenerator(BaseGenerator):
    __model__ = User

    @classmethod
    def generate_api_input_data(cls):
        return {
            'username': fake.simple_profile()['username'],
            'firstName': fake.first_name(),
            'lastName': fake.last_name(),
            'email': fake.email(),
            'password': fake.password(),
        }

    @classmethod
    def generate_model_obj_dict(cls):
        return {
            'username': fake.simple_profile()['username'],
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'password': fake.password(),
        }
