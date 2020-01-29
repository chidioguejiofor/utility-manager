from .base import (AbstractSchemaWithTimeStampsMixin, ImageField, StringField,
                   AlphaOnlyField, BaseSchema, AlphanumericField, PasswordField)
from ..models import User as UserModel
from marshmallow import fields


class ResetPasswordSchema(BaseSchema):
    __model__ = UserModel
    email = fields.Email(required=True)
    redirect_url = fields.URL(data_key='redirectURL',
                              load_only=True,
                              required=True)


class CompleteResetPasswordSchema(BaseSchema):
    __model__ = None
    password = PasswordField(load_only=True, required=True)
    reset_id = StringField(load_only=True, required=True, data_key='resetId')


class LoginSchema(BaseSchema):
    __model__ = None
    password = PasswordField(load_only=True, required=True)
    username_or_email = StringField(load_only=True,
                                    required=True,
                                    data_key='usernameOrEmail')

class ChangePasswordSchema(BaseSchema):
    current_password =  PasswordField(load_only=True, required=True, data_key='currentPassword')
    new_password =  PasswordField(load_only=True, required=True, data_key='newPassword')

class ProfileSchema(BaseSchema):
    username = AlphanumericField(data_key="username",
                                 min_length=1,
                                 max_length=20)
    first_name = AlphaOnlyField(
        data_key="firstName",
        min_length=3,
        max_length=20,
    )
    last_name = AlphaOnlyField(
        data_key="lastName",
        min_length=3,
        max_length=20,
    )
    image_url = fields.Url(
        data_key='imageURL',
        dump_only=True,
    )
    image = ImageField(
        data_key='image',
        load_only=True,
    )


class User(AbstractSchemaWithTimeStampsMixin, ResetPasswordSchema):
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
    image_url = fields.Url(
        data_key='imageURL',
        dump_only=True,
    )
    image = ImageField(
        data_key='image',
        load_only=True,
    )
    password = PasswordField(load_only=True, required=True)
    verified = fields.Boolean()
