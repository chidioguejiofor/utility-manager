from settings import db
from api.utils.exceptions import ModelOperationException
from api.utils.error_messages import model_operations, serialization_error
from .base import OrgBaseModel
from sqlalchemy.ext.declarative import declared_attr


class Unit(OrgBaseModel):
    name = db.Column(db.String(), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)
    __unique_constraints__ = ((('name', 'symbol', 'organisation_id'),
                               'unit_name_and_symbol_unique_constraint'), )
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Unit')
    parameters = db.relationship('Parameter', back_populates='unit')

    @classmethod
    def generate_table_args(cls):
        t_args = [*super().generate_table_args()]
        t_args.append(
            db.Index('unit_name_and_letter_when_org_is_null',
                     'name',
                     'symbol',
                     unique=True,
                     postgresql_where=(cls.organisation_id == None)), )
        return tuple(t_args)
