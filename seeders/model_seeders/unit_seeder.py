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
                 symbol,
                 created_at=None,
                 id=None,
                 updated_at=None):
        self.id = id if id else IDGenerator.generate_id()
        self.name = name
        self.symbol = symbol
        self.created_at = created_at if created_at else datetime.now(
            timezone.utc)
        if updated_at is not None:
            self.updated_at = dateutil.parser.parse(updated_at)
        else:
            self.updated_at = None

    def __eq__(self, other):
        they_are_equal = (self.name == other.name
                          and self.symbol == other.symbol)

        return they_are_equal

    def model_filter(self):
        symbol_check = np.bitwise_and.reduce([
            self.__model__.name == self.name,
            self.__model__.symbol == self.symbol
        ])

        return symbol_check

    def __repr__(self):
        return "%s(name=%r, symbol=%s, created_at=%s, updated_at=%s)" % (
            self.__class__.__name__,
            self.name,
            self.symbol,
            self.created_at,
            self.updated_at,
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
