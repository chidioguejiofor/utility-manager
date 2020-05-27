from settings import db
from .base import BaseModel
from api.utils.error_messages import serialization_error


class ApplianceParameter(BaseModel):
    _ORG_ID_NULLABLE = False
    appliance_id = db.Column(db.String(21), db.ForeignKey('Appliance.id'))

    parameter_id = db.Column(
        db.String(21),
        db.ForeignKey('Parameter.id'),
        nullable=False,
    )

    required = db.Column(db.Boolean(), nullable=False, default=False)
    appliance = db.relationship("Appliance",
                                back_populates='appliance_parameter',
                                lazy=True)

    parameter = db.relationship("Parameter",
                                back_populates='appliance_parameter',
                                lazy=True)

    __unique_constraints__ = ((('appliance_id', 'parameter_id'),
                               'appliance_parameter_unique_indx'), )

    __unique_violation_msg__ = serialization_error['already_added'].format(
        'parameter', 'Appliance')
