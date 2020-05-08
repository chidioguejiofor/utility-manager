from settings import db
from .base import OrgBaseModel, UserActionBase
from api.utils.error_messages import model_operations


class Appliance(UserActionBase, OrgBaseModel):
    _ORG_ID_NULLABLE = False

    label = db.Column(db.String(50), nullable=False)
    specs = db.Column(db.JSON, nullable=False)
    appliance_category_id = db.Column(db.String(21),
                                      db.ForeignKey('ApplianceCategory.id'))
    appliance_category = db.relationship("ApplianceCategory",
                                         back_populates='appliance',
                                         lazy=True)
    appliance_parameter = db.relationship("ApplianceParameter",
                                          back_populates='appliance',
                                          lazy=True)
    logs = db.relationship("Log", back_populates='appliance', lazy=True)
    __unique_constraints__ = ((('label', 'organisation_id',
                                'appliance_category_id'),
                               'org_appliance_constraint'), )
    __unique_violation_msg__ = model_operations['appliance_already_exists']
