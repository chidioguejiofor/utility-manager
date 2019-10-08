import os
import jwt
from datetime import datetime, timedelta
from api.utils.constants import LOGIN_TOKEN


class TokenValidator:
    SECRET = os.getenv('JWT_SECRET')

    @classmethod
    def decode_token(cls, token, token_type, verify=True):
        token_data = jwt.decode(token,
                                cls.SECRET,
                                algorithms=['HS256'],
                                verify=verify)
        if token_data['data']['type'] == token_type:

            return token_data['data']

        # raise jwt.exceptions.PyJWTError()

    @classmethod
    def create_token(cls, token_data, **timedelta_kwargs):
        if not timedelta_kwargs:
            timedelta_kwargs = {'days': 2}

        payload = {
            'data': token_data,
            'exp': datetime.utcnow() + timedelta(**timedelta_kwargs)
        }
        return jwt.encode(payload, cls.SECRET,
                          algorithm='HS256').decode('utf-8')
