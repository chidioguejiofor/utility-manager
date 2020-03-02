from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, fields)
from ..models import ApplianceCategory as ApplianceCategoryModel


class ApplianceCategory(BaseSchema, AbstractSchemaWithTimeStampsMixin,
                        AbstractUserActionMixin):
    __model__ = ApplianceCategoryModel
    name = StringField(max_length=50,
                       min_length=2,
                       required=True,
                       capitalize=True)
    description = StringField(required=True)
    organisation_id = StringField(required=True)
    editable = fields.Function(lambda obj: bool(obj.organisation_id),
                               dump_only=True)
