from flask import request
from .base import BaseView, CookieGeneratorMixin
from settings import endpoint
from api.schemas import UserSchema, ProfileSchema
from api.utils.success_messages import RETRIEVED, UPDATED
from api.utils.error_messages import serialization_error
from api.models import User
from api.utils.exceptions import ResponseException


@endpoint('/user/profile')
class Profile(BaseView):
    PROTECTED_METHODS = ['GET', 'PATCH']
    unverified_methods = ['GET', 'PATCH']

    def get(self, user_data):
        user = User.query.get(user_data['id'])

        user_data = UserSchema().dump_success_data(user,
                                                   RETRIEVED.format("Profile"))
        return user_data, 200

    def patch(self, user_data):
        image = request.files.get('image')
        form_dict = {**request.form}
        if image:
            form_dict['image'] = image

        schema = ProfileSchema()
        new_user_dict = schema.load(form_dict)
        data_to_update = ['username', 'first_name', 'last_name', 'image']

        update_dict = {}
        user_to_update = User.query.get(user_data['id'])
        for key in data_to_update:
            value = new_user_dict.get(key)
            if value:
                update_dict[key] = value
                setattr(user_to_update, key, value)

        if update_dict:
            user_to_update.update()
        else:
            raise ResponseException(serialization_error['empty_update_data'])

        user_data = UserSchema().dump_success_data(user_to_update,
                                                   UPDATED.format("Profile"))
        return user_data, 201
