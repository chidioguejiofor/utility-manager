from settings import db
from .base import BaseModel


class Unit(BaseModel):
    name = db.Column(db.String(), nullable=False)
    symbol = db.Column(db.String(5), nullable=False)
    __unique_constraints__ = ((('name', 'symbol'),
                               'unit_name_and_symbol_unique_constraint'), )
