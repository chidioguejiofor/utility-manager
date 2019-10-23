from . import fake, BaseGenerator
from api.models import User
from api.utils.token_validator import TokenValidator
from api.utils.constants import LOGIN_TOKEN


class UserGenerator(BaseGenerator):
    __model__ = User

    @classmethod
    def generate_api_input_data(cls):
        return {
            'username': fake.simple_profile()['username'][:20],
            'firstName': fake.first_name()[:20],
            'lastName': fake.last_name()[:20],
            'email': fake.email(),
            'password': fake.password(),
            'redirectURL': fake.url(),
        }

    @staticmethod
    def generate_token(user, token_type=LOGIN_TOKEN, **time_kwargs):
        url_key = 'redirectURL' if token_type == LOGIN_TOKEN else 'redirect_url'
        return TokenValidator.create_token(
            {
                'id': user.id,
                'email': user.email,
                url_key: user.redirect_url,
                'type': token_type,
                'verified': user.verified
            }, **time_kwargs)

    @classmethod
    def generate_model_obj_dict(cls, verified=False):
        return {
            'username': fake.simple_profile()['username'][:20],
            'first_name': fake.first_name()[:20],
            'last_name': fake.last_name()[:20],
            'email': fake.email(),
            'password': fake.password(),
            'verified': verified,
        }
