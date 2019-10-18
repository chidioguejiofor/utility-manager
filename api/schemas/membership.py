from marshmallow import fields
from marshmallow_enum import EnumField
from .base import BaseSchema
from ..models import RoleEnum
from .organisation import Organisation
from .user import User


class _OrgMembershipSchema(BaseSchema):
    member = fields.Nested(User)
    role = EnumField(enum=RoleEnum, by_value=False)


class OrganisationMembership(Organisation):
    memberships = fields.Nested(_OrgMembershipSchema, many=True)


class _UserMembershipSchema(BaseSchema):
    from .organisation import Organisation as OrganisationSchema
    organisation = fields.Nested(OrganisationSchema)
    role = EnumField(enum=RoleEnum, by_value=False)


class UserMembership(User):
    memberships = fields.Nested(_UserMembershipSchema, many=True)