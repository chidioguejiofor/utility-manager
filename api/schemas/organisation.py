from .base import BaseSchema, StringField, AlphanumericField
from ..models import Organisation as OrganisationModel, SubscriptionEnum
from marshmallow import fields
from marshmallow_enum import EnumField


class Organisation(BaseSchema):
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
