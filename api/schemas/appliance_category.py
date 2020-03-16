from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, fields)
from ..models import ApplianceCategory as ApplianceCategoryModel
from .user import User


class ApplianceCategory(AbstractUserActionMixin,
                        AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = ApplianceCategoryModel
    _excluded_user_fields = ['created_at', 'updated_at', 'verified']
    name = StringField(max_length=50,
                       min_length=2,
                       required=True,
                       capitalize=True)
    description = StringField(required=True)
    organisation_id = StringField(required=True, load_only=True)
    editable = fields.Function(lambda obj: bool(obj.organisation_id),
                               dump_only=True)

    created_by = fields.Nested(User(exclude=_excluded_user_fields),
                               dump_only=True,
                               data_key='createdBy')
    updated_by = fields.Nested(User(exclude=_excluded_user_fields),
                               dump_only=True,
                               data_key='updatedBy')
