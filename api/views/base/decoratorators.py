from api.utils.exceptions import ResponseException
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors, serialization_error
from api.utils.constants import LOGIN_TOKEN, COOKIE_TOKEN_KEY, REDIS_TOKEN_HASH_KEY
from api.models import Membership

from functools import wraps
from flask import request


class Authentication:
    def __init__(self, view):
        self.view = view

    def _decode_token(self, check_user_is_verified=False):
        """Decoded a token and returns the decoded data

        Args:
            token_type (int, optional): The type of token being decoded
                Defaults to `1`(LOGIN_TOKEN)
            check_user_is_verified (bool): When this is true, this ensures that
                the user is also verified

        Returns:
            dict, str: The decoded token data
        """
        from api.services.redis_util import RedisUtil
        cookie_value = request.cookies.get(COOKIE_TOKEN_KEY)

        if not cookie_value or len(cookie_value.split('/')) != 2:
            raise ResponseException(
                authentication_errors['token_error'],
                401,
            )
        user_id, token_id = cookie_value.split('/')
        redis_hash = f'{user_id}_{REDIS_TOKEN_HASH_KEY}'
        token = RedisUtil.hget(redis_hash, token_id)
        decoded_data = TokenValidator.decode_token_data(token,
                                                        token_type=LOGIN_TOKEN)
        if check_user_is_verified and not decoded_data['verified']:
            raise ResponseException(
                authentication_errors['unverified_user'],
                403,
            )
        return decoded_data

    def _authenticate_user(self):
        view = self.view
        method = request.method.upper()

        if method in view.protected_methods:
            verified_user_only = not (method in view.unverified_methods)
            return self._decode_token(
                check_user_is_verified=verified_user_only)
        return None

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_data = self._authenticate_user()
            if user_data:
                return func(*args, **kwargs, user_data=user_data)
            return func(*args, **kwargs)

        return wrapper


class OrgViewDecorator:
    def __init__(self, view):
        self.view = view

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_data = kwargs.get('user_data')
            org_id = kwargs.get('org_id')
            membership = Membership.eager('role', 'member')\
                .filter_by(
                organisation_id=org_id, user_id=user_data['id']).first()

            if not membership:
                raise ResponseException(
                    message=serialization_error['not_found'].format(
                        'Organisation'),
                    status_code=404,
                )

            allowed_roles = self.view.ALLOWED_ROLES.get(request.method.upper())

            if allowed_roles and membership.role.name not in allowed_roles:
                raise ResponseException(
                    message=authentication_errors['forbidden'],
                    status_code=403,
                )

            return func(*args, **kwargs, membership=membership)

        return wrapper
