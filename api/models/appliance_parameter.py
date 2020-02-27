from settings import db
from .base import UserActionBase, OrgBaseModel
from api.utils.error_messages import serialization_error


class ApplianceParameter(OrgBaseModel, UserActionBase):
    _ORG_ID_NULLABLE = False
    appliance_id = db.Column(db.String(21), db.ForeignKey('Appliance.id'))

    parameter_id = db.Column(
        db.String(21),
        db.ForeignKey('Parameter.id'),
        nullable=False,
    )
    appliance = db.relationship("Appliance")
    parameter = db.relationship("Parameter")

    __unique_constraints__ = ((('appliance_id', 'parameter_id',
                                'organisation_id'),
                               'appliance_parameter_unique_indx'), )

    __unique_violation_msg__ = serialization_error['already_added'].format(
        'parameter', 'Appliance')
