import dateutil.parser
import numpy as np
from api.models import Unit
from api.utils.id_generator import IDGenerator
from datetime import datetime, timezone
from .base import BaseSeeder


class UnitSeed(BaseSeeder):
    __model__ = Unit
    KEY = 'unit'

    def __init__(self,
                 name,
                 greek_symbol_num,
                 letter_symbol,
                 created_at=None,
                 id=None,
                 updated_at=None):
        self.id = id if id else IDGenerator.generate_id()
        self.name = name
        self.greek_symbol_num = int(
            greek_symbol_num) if greek_symbol_num else None
        self.letter_symbol = letter_symbol
        self.created_at = created_at if created_at else datetime.now(
            timezone.utc)
        if updated_at is not None:
            self.updated_at = dateutil.parser.parse(updated_at)
        else:
            self.updated_at = None

    def __eq__(self, other):
        they_are_equal = ((self.name == other.name
                           and self.greek_symbol_num == other.greek_symbol_num)
                          or (self.name == other.name
                              and self.letter_symbol == other.letter_symbol))

        return they_are_equal

    def model_filter(self):
        greek_check = np.bitwise_and.reduce([
            self.__model__.name == self.name,
            self.__model__.greek_symbol_num == self.greek_symbol_num
        ])
        letter_check = np.bitwise_and.reduce([
            self.__model__.name == self.name,
            self.__model__.letter_symbol == self.letter_symbol
        ])
        filter_obj = greek_check | letter_check

        return filter_obj

    def __repr__(self):
        return "%s(name=%r, greek_symbol_num=%r, letter_symbol=%s, created_at=%s, updated_at=%s)" % (
            self.__class__.__name__,
            self.name,
            self.greek_symbol_num,
            self.letter_symbol,
            self.created_at,
            self.updated_at,
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'greek_symbol_num': self.greek_symbol_num,
            'letter_symbol': self.letter_symbol,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
