import enum
from settings import db
from .base import OrgBaseModel, UserActionBase
from api.utils.error_messages import serialization_error


class ValueType(enum.Enum):
    NUMERIC = 0
    STRING = 1
    DATE_TIME = 2
    DATE = 3
    ENUM = 4


class Parameter(UserActionBase, OrgBaseModel):

    name = db.Column(db.String(), nullable=False)
    unit_id = db.Column(db.String(),
                        db.ForeignKey('Unit.id', ondelete='RESTRICT'),
                        nullable=True)
    validation = db.Column(db.String(), nullable=True)
    required = db.Column(db.BOOLEAN, default=True, nullable=False)
    value_type = db.Column(db.Enum(ValueType, name='value_type_enum'),
                           nullable=False)
    unit = db.relationship('Unit',
                           back_populates='parameters',
                           foreign_keys=[unit_id])

    __back_populates__kwargs__ = {
        'updated_by': 'updated_parameters',
        'created_by': 'created_parameters',
    }
    __unique_constraints__ = ((('name', 'organisation_id'),
                               'parameter_name_and_org_unique_constraint'), )
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Parameter')
