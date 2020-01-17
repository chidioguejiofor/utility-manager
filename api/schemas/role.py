from .base import AbstractSchemaWithTimeStampsMixin, AlphanumericField, BaseSchema, StringField
from .base import BaseSchema
from ..models import Role as RoleModel
from .organisation import Organisation
from .user import User


class Role(BaseSchema):
    __model__ = RoleModel
    name = StringField(max_length=10, min_length=3)
    description = StringField()
