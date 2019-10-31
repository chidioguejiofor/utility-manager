from settings import db
from api.utils.exceptions import ModelOperationException
from api.utils.error_messages import model_operations
from .base import BaseModel


class Unit(BaseModel):
    name = db.Column(db.String(), nullable=False)
    letter_symbol = db.Column(db.String(5), nullable=True)
    greek_symbol_num = db.Column(db.SmallInteger(), nullable=True)
    __unique_constraints__ = (
        (('name', 'letter_symbol'),
         'unit_name_and_letter_symbol_unique_constraint'),
        (('name', 'greek_symbol_num'),
         'unit_name_and_greeksymbolnum_unique_constraint'),
    )
    parameters = db.relationship('Parameter', back_populates='unit')

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
