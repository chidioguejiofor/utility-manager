from .base import fake, BaseGenerator
from api.models import Organisation
from .user import UserGenerator


class OrganisationGenerator(BaseGenerator):
    __model__ = Organisation

    @classmethod
    def generate_api_input_data(cls):
        return {
            'name': fake.first_name(),
            'website': fake.url(),
            'address': fake.address(),
            'displayName': fake.first_name(),
        }

    @classmethod
    def generate_model_obj_dict(cls, creator_id=None, verify_user=True):
        if not creator_id:
            creator_id = UserGenerator.generate_model_obj(
                save=True, verified=verify_user).id
        return {
            'name': fake.first_name(),
            'website': fake.url(),
            'address': fake.address(),
            'display_name': fake.first_name(),
            'creator_id': creator_id,
        }
