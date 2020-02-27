from marshmallow import fields
from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, ListField, IDField)
from ..models import ApplianceCategory as ApplianceCategoryModel


class Appliance(BaseSchema, AbstractSchemaWithTimeStampsMixin,
                AbstractUserActionMixin):
    label = StringField(max_length=50,
                        min_length=2,
                        required=True,
                        capitalize=True)
    specs = fields.Dict(required=True)
    parameters = ListField(IDField, min_length=1, required=True)
