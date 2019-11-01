from .base import (AbstractSchemaWithTimeStampsMixin, AlphaOnlyField,
                   AlphanumericField, BaseSchema, StringField)
from marshmallow import fields, validate
from ..models import Unit as UnitModel


class Unit(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = UnitModel
    name = AlphanumericField(allow_spaces=True, required=True, capitalize=True)
    letter_symbol = AlphaOnlyField(max_length=5,
                                   data_key='letterSymbol',
                                   allow_spaces=False)
    greek_symbol_num = fields.Integer(data_key='greekSymbol',
                                      validate=validate.Range(min=1, max=48))
    organisation_id = StringField(data_key='organisationId', required=True)
