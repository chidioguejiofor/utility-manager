from marshmallow import fields
from marshmallow_enum import EnumField
from .base import BaseSchema, StringField
from api.services.redis_util import RedisUtil
from .organisation import Organisation
from .user import User
from .role import Role


class _OrgMembershipSchema(BaseSchema):
    member = fields.Nested(User)
    role = fields.Nested(Role)


class OrganisationMembership(Organisation):
    memberships = fields.Nested(_OrgMembershipSchema, many=True)


class OrgAndMembershipSchema(BaseSchema):
    from .organisation import Organisation as OrganisationSchema
    organisation = fields.Nested(OrganisationSchema(exclude=['creator']))
    role = fields.Nested(Role)


class UserMembership(User):
    memberships = fields.Nested(OrgAndMembershipSchema, many=True)
