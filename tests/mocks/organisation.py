from . import fake, BaseGenerator
from api.models import Organisation


class OrganisationGenerator(BaseGenerator):
    __model__ = Organisation

    @classmethod
    def generate_api_input_data(cls):
        return {
            'name': fake.first_name(),
            'website': fake.url(),
            'address': fake.address(),
            'email': fake.email(),
            'displayName': fake.first_name(),
        }

    @classmethod
    def generate_model_obj_dict(cls):
        return {
            'name': fake.first_name(),
            'website': fake.url(),
            'address': fake.address(),
            'email': fake.email(),
            'display_name': fake.first_name(),
        }
