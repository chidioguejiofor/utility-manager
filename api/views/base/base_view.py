import os
from flask_restplus import Resource
from flask import request
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors
from api.utils.constants import LOGIN_TOKEN


class BaseView(Resource):
    def decode_token(self):
        """Decoded a token and returns the decoded data

        Args:
            token_type (int, optional): The type of token being decoded
                Defaults to `1`(LOGIN_TOKEN)

        Returns:
            dict, str: The decoded token data
        """
        token = request.cookies.get('token')
        if not token:
            raise MessageOnlyResponseException(
                authentication_errors['missing_token'],
                401,
            )

        return TokenValidator.decode_token_data(token, token_type=LOGIN_TOKEN)


class CookieGeneratorMixin:
    def generate_cookie_header(self, user_data):
        secure_flag = '; secure' if os.getenv(
            'FLASK_ENV') != 'development' else ''

        payload = {
            'type': LOGIN_TOKEN,
            'email': user_data['email'],
            'id': user_data['id'],
            'username': user_data['username'],
            "verified": user_data['verified'],
        }
        token = TokenValidator.create_token(payload)
        return {'Set-Cookie': f'token={token}; HttpOnly{secure_flag}'}
