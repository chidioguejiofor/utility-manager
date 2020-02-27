from settings import db
from .base import OrgBaseModel, UserActionBase
from api.utils.error_messages import serialization_error


class Appliance(UserActionBase, OrgBaseModel):
    _ORG_ID_NULLABLE = False
    label = db.Column(db.String(50), nullable=False)
    specs = db.Column(db.JSON, nullable=False)
    appliance_category_id = db.Column(db.String(21),
                                      db.ForeignKey('ApplianceCategory.id'))
    appliance_category = db.relationship("ApplianceCategory")
    __unique_constraints__ = ((('label', 'organisation_id',
                                'appliance_category_id'),
                               'org_appliance_constraint'), )
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Appliance')
