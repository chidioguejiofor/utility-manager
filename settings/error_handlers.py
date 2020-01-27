from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.exceptions import UniqueConstraintException, ResponseException, ModelOperationException
from marshmallow.exceptions import ValidationError
import logging
from jwt.exceptions import PyJWTError, ExpiredSignature
import werkzeug.exceptions


def create_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_errors(error):
        if '_schema' in error.messages:
            error.messages = error.messages['_schema']
        return {
            'status': 'error',
            'errors': error.messages,
            'message': serialization_error['invalid_field_data']
        }, 400

    @app.errorhandler(ResponseException)
    def handle_errors(error):
        error_dict = {
            'status': 'error',
            'message': error.message,
        }

        if error.errors:
            error_dict['errors'] = error.errors

        return error_dict, error.status_code

    @app.errorhandler(ModelOperationException)
    def handle_errors(error):
        return {
            'status': 'error',
            'message': error.api_message,
        }, error.status_code

    @app.errorhandler(PyJWTError)
    def handle_errors(error):
        if isinstance(error, ExpiredSignature):
            return {
                'status': 'error',
                'message': authentication_errors['session_expired'],
            }, 401
        else:
            return {
                'status': 'error',
                'message': authentication_errors['token_invalid'],
            }, 401

    @app.errorhandler(UniqueConstraintException)
    def handle_unique_errors(error):
        return {'status': 'error', 'message': error.message}, 409

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def handle_resource_not_found(error):
        return {'status': 'error', 'message': 'Resource was not found'}, 404

    @app.errorhandler(Exception)
    def handle_any_other_errors(error):
        logging.exception(error)
        return {'status': 'error', 'message': 'Unknown Error'}, 500
