import jwt
import os
from .base import BaseView
from settings import endpoint
from flask import request
from api.utils.error_messages import serialization_error
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.models import User
from api.schemas import UserSchema
from api.utils.success_messages import CREATED, LOGIN


@endpoint('/auth/register')
class Register(BaseView):
    @staticmethod
    def post():
        user_obj = UserSchema().load(request.get_json())
        user_obj.save()
        return UserSchema().dump_success_data(user_obj,
                                              CREATED.format('user')), 201


@endpoint('/auth/login')
class Login(BaseView):
    @staticmethod
    def post():
        data = request.get_json()
        username_or_email = data.get('usernameOrEmail')
        password = data.get('password')

        query_by_email = '@' in username_or_email
        if query_by_email:
            user = User.query.filter_by(email=username_or_email).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()

        if user and user.verify_password(password):
            user_json = UserSchema().dump_success_data(user,
                                                       LOGIN.format('user'))

            token = TokenValidator.create_token(user_json['data'])
            secure_flag = '; secure' if os.getenv(
                'FLASK_ENV') != 'development' else ''
            headers = {'Set-Cookie': f'token={token}; HttpOnly{secure_flag}'}
            return user_json, 200, headers

        raise MessageOnlyResponseException(
            message=serialization_error['login_failed'],
            status_code=400,
        )
