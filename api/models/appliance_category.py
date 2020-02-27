from settings import db
from .base import OrgBaseModel, UserActionBase
from api.utils.error_messages import serialization_error


class ApplianceCategory(UserActionBase, OrgBaseModel):
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String, nullable=False)
    __unique_constraints__ = ((('name', 'organisation_id'),
                               'app_category_org_constraint'), )
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Appliance Category')
