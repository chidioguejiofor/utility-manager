import os
import jwt
from datetime import datetime, timedelta


class TokenValidator:
    SECRET = os.getenv('JWT_SECRET')

    @classmethod
    def decode_token(cls, token):
        return jwt.decode(token, cls.SECRET, algorithms=['HS256'])

    @classmethod
    def create_token(cls, user_json, **timedelta_kwargs):
        if not timedelta_kwargs:
            timedelta_kwargs = {'days': 2}

        payload = {
            'data': {
                'email': user_json['email'],
                'id': user_json['id'],
                'username': user_json['username'],
                "verified": user_json['verified'],
            },
            'exp': datetime.utcnow() + timedelta(**timedelta_kwargs)
        }
        return jwt.encode(payload, cls.SECRET,
                          algorithm='HS256').decode('utf-8')
