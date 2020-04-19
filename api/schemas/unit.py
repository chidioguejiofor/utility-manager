from .base import (AbstractSchemaWithTimeStampsMixin, AlphaOnlyField,
                   AlphanumericField, BaseSchema, StringField)
from marshmallow import fields, validate
from ..models import Unit as UnitModel


class Unit(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = UnitModel
    name = AlphanumericField(allow_spaces=True, required=True, capitalize=True)
    symbol = AlphaOnlyField(max_length=5,
                            data_key='symbol',
                            allow_spaces=False)
    organisation_id = StringField(data_key='organisationId', required=True)
