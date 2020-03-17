from settings import db
from api.utils.exceptions import ModelOperationException
from api.utils.error_messages import model_operations, serialization_error
from .base import OrgBaseModel
from sqlalchemy.ext.declarative import declared_attr


class Unit(OrgBaseModel):
    name = db.Column(db.String(), nullable=False)
    letter_symbol = db.Column(db.String(5), nullable=True)
    greek_symbol_num = db.Column(db.SmallInteger(), nullable=True)
    __unique_constraints__ = (
        (('name', 'letter_symbol', 'organisation_id'),
         'unit_name_and_letter_symbol_unique_constraint'),
        (('name', 'greek_symbol_num', 'organisation_id'),
         'unit_name_and_greeksymbolnum_unique_constraint'),
    )
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Unit')
    parameters = db.relationship('Parameter', back_populates='unit')

    @classmethod
    def generate_table_args(cls):
        t_args = [*super().generate_table_args()]
        t_args.append(
            db.Index('unit_name_and_letter_when_org_is_null',
                     'name',
                     'letter_symbol',
                     unique=True,
                     postgresql_where=(cls.organisation_id == None)), )
        t_args.append(
            db.Index('unit_name_and_greek_symbol_when_org_is_null',
                     'name',
                     'greek_symbol_num',
                     unique=True,
                     postgresql_where=(cls.organisation_id == None)), )
        return tuple(t_args)

    def save(self, *args, **kwargs):
        if self.letter_symbol is None and self.greek_symbol_num is None:
            raise ModelOperationException(
                status_code=400,
                message=model_operations['both_greek_and_letter_are_none'][0],
                api_message=model_operations['both_greek_and_letter_are_none']
                [1],
            )
        elif self.letter_symbol is not None and self.greek_symbol_num is not None:
            raise ModelOperationException(
                status_code=400,
                message=model_operations['both_greek_and_letter_are_provided']
                [0],
                api_message=model_operations[
                    'both_greek_and_letter_are_provided'][1],
            )
        super().save(*args, **kwargs)
