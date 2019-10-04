from flask_restplus import Resource
from flask import request
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors


class BaseView(Resource):
    protected_methods = []

    def decode_user_token(self):
        if request.method not in self.protected_methods:
            return

        token = request.cookies.get('token')
        if not token:
            raise MessageOnlyResponseException(
                authentication_errors['missing_token'],
                401,
            )

        user = TokenValidator.decode_token(token)
        return user
