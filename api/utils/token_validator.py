import os
import jwt
from datetime import datetime, timedelta
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.error_messages import authentication_errors


class TokenValidator:
    SECRET = os.getenv('JWT_SECRET')

    @classmethod
    def decode_token_data(cls, token, token_type, verify=True):
        return cls.decode_token(token, token_type, verify)['data']

    @classmethod
    def decode_token(cls, token, token_type, verify=True):
        token_data = jwt.decode(token,
                                cls.SECRET,
                                algorithms=['HS256'],
                                verify=verify)
        if token_data['data']['type'] == token_type:
            return token_data

        raise jwt.exceptions.PyJWTError()

    @classmethod
    def create_token(cls, token_data, **timedelta_kwargs):
        if not timedelta_kwargs:
            timedelta_kwargs = {'days': 2}
        current_time = datetime.utcnow()
        payload = {
            'data': token_data,
            'exp': current_time + timedelta(**timedelta_kwargs),
            'iat': current_time,
        }
        return jwt.encode(payload, cls.SECRET,
                          algorithm='HS256').decode('utf-8')
