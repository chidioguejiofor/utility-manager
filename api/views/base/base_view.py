import os
from flask_restplus import Resource
from flask import request
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors
from api.utils.constants import LOGIN_TOKEN


class BaseView(Resource):
    def decode_token(self, check_user_is_verified=False):
        """Decoded a token and returns the decoded data

        Args:
            token_type (int, optional): The type of token being decoded
                Defaults to `1`(LOGIN_TOKEN)
            check_user_is_verified (bool): When this is true, this ensures that
                the user is also verified

        Returns:
            dict, str: The decoded token data
        """
        token = request.cookies.get('token')
        if not token:
            raise MessageOnlyResponseException(
                authentication_errors['missing_token'],
                401,
            )
        decoded_data = TokenValidator.decode_token_data(token,
                                                        token_type=LOGIN_TOKEN)
        if check_user_is_verified and not decoded_data['verified']:
            raise MessageOnlyResponseException(
                authentication_errors['unverified_user'],
                403,
            )
        return decoded_data


class CookieGeneratorMixin:
    def generate_cookie_header(self, user_data=None, expired=False):
        """Generates a dict that contains headers with cookie

        When expired is False, it uses the user_data to generate a token
        and puts it in the cookie of the response.

        When expired is True, it invalidates the previously sent token
        Args:
            user_data dict: User data that would be used to generate token
            expired bool: when True, token would be expired

        Returns:

        """
        secure_flag = 'secure' if os.getenv(
            'FLASK_ENV') != 'development' else ''

        token = 'deleted'
        expired_str = 'expires=Thu, 01 Jan 1970 00:00:00 GMT'
        if not expired:
            expired_str = ''
            payload = {
                'type': LOGIN_TOKEN,
                'email': user_data['email'],
                'id': user_data['id'],
                'username': user_data['username'],
                "verified": user_data['verified'],
            }
            token = TokenValidator.create_token(payload)
        return {
            'Set-Cookie':
            f'token={token}; path=/; HttpOnly; {secure_flag}; {expired_str}'
        }
