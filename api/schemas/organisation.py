from marshmallow import fields
from marshmallow_enum import EnumField
from .base import AbstractSchemaWithTimeStamps, StringField, AlphanumericField, BaseSchema
from ..models import Organisation as OrganisationModel, SubscriptionEnum, RoleEnum


class Organisation(AbstractSchemaWithTimeStamps):
    __model__ = OrganisationModel
    name = AlphanumericField(min_length=2, max_length=120, allow_spaces=True)
    website = StringField()
    address = StringField()
    email = fields.Email()
    display_name = StringField(data_key='displayName', max_length=25)
    password = StringField(load_only=True)
    subscription_type = EnumField(
        enum=SubscriptionEnum,
        data_key='subscriptionType',
        dump_only=True,
        by_value=True,
    )
    logo_url = fields.Url(
        data_key='logoUrl',
        dump_only=True,
    )


class _MembershipSchema(BaseSchema):
    from .user import User as UserSchema
    member = fields.Nested(UserSchema)
    role = EnumField(enum=RoleEnum, by_value=False)


class OrganisationMembership(Organisation):
    memberships = fields.Nested(_MembershipSchema, many=True)
