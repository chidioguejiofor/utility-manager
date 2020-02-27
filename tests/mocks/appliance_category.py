from . import fake, BaseGenerator
from api.models import ApplianceCategory
from .user import UserGenerator


class ApplianceCategoryGenerator(BaseGenerator):
    __model__ = ApplianceCategory

    @classmethod
    def generate_api_input_data(cls):
        return {
            'name': fake.name()[:30],
            'description': fake.text()[:30].strip()
        }

    @classmethod
    def generate_model_obj_dict(cls, org_id):
        return {
            **cls.generate_api_input_data(),
            'organisation_id': org_id,
        }
