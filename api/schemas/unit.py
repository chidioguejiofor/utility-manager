from .base import AbstractSchemaWithTimeStampsMixin, AlphaOnlyField, AlphanumericField, BaseSchema, ImageField
from ..models import Unit as UnitModel


class Unit(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = UnitModel
    name = AlphanumericField(allow_spaces=True)
    symbol = AlphaOnlyField(max_length=5, allow_spaces=False, capitalize=True)
