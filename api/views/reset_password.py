import jwt
from .base import BaseView
from settings import endpoint
from flask import request

from api.utils.error_messages import serialization_error, authentication_errors, password_change_errors
from api.utils.exceptions import ResponseException
from api.utils.token_validator import TokenValidator
from api.models import User
from api.schemas import ResetPasswordSchema, CompleteResetPasswordSchema, ChangePasswordSchema
from api.utils.success_messages import RESET_PASS_MAIL, PASSWORD_CHANGED
from api.utils.constants import RESET_TOKEN, RESET_PASSWORD_SUBJECT

from api.services.redis_util import RedisUtil


@endpoint('/auth/reset')
class ForgotPassword(BaseView):
    def patch(self):
        from api.utils.emails import EmailUtil
        obj = ResetPasswordSchema().load(request.get_json(()))

        user = User.query.filter_by(email=obj.email).first()
        if not user:
            raise ResponseException(serialization_error['email_not_found'],
                                    404)
        EmailUtil.send_verification_email_to_user(
            user,
            token_type=RESET_TOKEN,
            template_name='reset-email',
            link_url=f'{obj.redirect_url}',
            subject=RESET_PASSWORD_SUBJECT)

        return {
            'status': 'success',
            'message': RESET_PASS_MAIL.format(user.email)
        }, 200


@endpoint('/auth/reset/confirm')
class ConfirmResetPassword(BaseView):
    def patch(self):
        loaded_data = CompleteResetPasswordSchema().load(request.get_json())
        token = RedisUtil.get_key(loaded_data['reset_id'])
        try:
            token_data = TokenValidator.decode_token_data(token, RESET_TOKEN)
        except jwt.exceptions.PyJWTError:
            raise ResponseException(
                authentication_errors['invalid_reset_link'], 400)
        finally:
            if token:
                RedisUtil.delete_key(loaded_data['reset_id'])

        user = User.query.get(token_data['id'])
        user.password = loaded_data['password']
        user.update()
        return {'status': 'success', 'message': PASSWORD_CHANGED}


@endpoint('/auth/password')
class LoggedInUserChangePassword(BaseView):
    protected_methods = ['PATCH']
    unverified_methods = ['PATCH']

    @staticmethod
    def patch(user_data):
        data = ChangePasswordSchema().load(request.get_json())
        if data['current_password'] == data['new_password']:
            raise ResponseException(message=password_change_errors[
                'new_pass_and_change_pass_are_eq'])
        user = User.query.get(user_data['id'])

        if not user.verify_password(data['current_password']):
            raise ResponseException(
                message=password_change_errors['current_pass_is_invalid'])
        user.password = data['new_password']
        user.update()
        return {'status': 'success', 'message': PASSWORD_CHANGED}
