from flask_restplus import Resource
from api.utils.validators.token_validator import TokenValidator


class BaseView(Resource):
    method_decorators = [TokenValidator.validate_token]
