from settings import db
from .base import OrgBaseModel, UserActionBase, BaseModel
from api.utils.error_messages import serialization_error


class Log(UserActionBase, OrgBaseModel):
    _ORG_ID_NULLABLE = False
    appliance_id = db.Column(db.String(21),
                             db.ForeignKey('Appliance.id'),
                             nullable=False)
    appliance = db.relationship("Appliance", back_populates='logs', lazy=True)
    log_values = db.relationship("LogValue", back_populates='log', lazy=True)
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Log')


class LogValue(BaseModel):
    text_value = db.Column(db.String)
    numeric_value = db.Column(db.Float(precision=2), nullable=True)
    parameter_id = db.Column(
        db.String(21),
        db.ForeignKey('Parameter.id'),
        nullable=False,
    )
    log_id = db.Column(
        db.String(21),
        db.ForeignKey('Log.id', ondelete='CASCADE'),
        nullable=False,
    )
    log = db.relationship("Log", back_populates='log_values', lazy=True)
