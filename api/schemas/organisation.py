from marshmallow import fields
from marshmallow_enum import EnumField
from .base import AbstractSchemaWithTimeStampsMixin, StringField, AlphanumericField, BaseSchema, ImageField
from ..models import Organisation as OrganisationModel, SubscriptionEnum
from .user import User


class Organisation(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = OrganisationModel
    name = AlphanumericField(min_length=2, max_length=120, allow_spaces=True)
    website = StringField(required=True)
    address = StringField(required=True)
    display_name = StringField(data_key='displayName',
                               max_length=25,
                               required=True)
    subscription_type = EnumField(enum=SubscriptionEnum,
                                  data_key='subscriptionType',
                                  dump_only=True,
                                  by_value=True,
                                  required=True)
    image_url = fields.Url(
        data_key='logoUrl',
        dump_only=True,
    )
    logo = ImageField(
        data_key='logo',
        load_only=True,
        required=True,
    )

    creator = fields.Nested(User)
