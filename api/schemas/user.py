from .base import AbstractSchemaWithTimeStamps, StringField, AlphaOnlyField, BaseSchema, AlphanumericField
from ..models import User as UserModel, RoleEnum
from marshmallow import fields
from marshmallow_enum import EnumField


class User(AbstractSchemaWithTimeStamps):
    __model__ = UserModel
    username = AlphanumericField(data_key="username",
                                 min_length=1,
                                 max_length=20,
                                 required=True)
    first_name = AlphaOnlyField(data_key="firstName",
                                min_length=3,
                                max_length=20,
                                required=True)
    last_name = AlphaOnlyField(data_key="lastName",
                               min_length=3,
                               max_length=20,
                               required=True)
    password = StringField(load_only=True, required=True)
    email = fields.Email(required=True)
    verified = fields.Boolean()


class _MembershipSchema(BaseSchema):
    from .organisation import Organisation as OrganisationSchema
    organisation = fields.Nested(OrganisationSchema)
    role = EnumField(enum=RoleEnum, by_value=False)


class UserWithMembership(User):
    memberships = fields.Nested(_MembershipSchema, many=True)
