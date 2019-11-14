import jwt
from .base import BaseView
from settings import endpoint
from flask import request

from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.models import User
from api.schemas import ResetPasswordSchema, CompleteResetPasswordSchema
from api.utils.success_messages import RESET_PASS_MAIL, PASSWORD_CHANGED
from api.utils.constants import RESET_TOKEN, RESET_PASSWORD_SUBJECT

from api.services.redis_util import RedisUtil


@endpoint('/auth/reset')
class ResetPassword(BaseView):
    def patch(self):
        from api.utils.emails import EmailUtil
        obj = ResetPasswordSchema().load(request.get_json(()))

        user = User.query.filter_by(email=obj.email).first()
        if not user:
            raise MessageOnlyResponseException(
                serialization_error['email_not_found'], 404)
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
            raise MessageOnlyResponseException(
                authentication_errors['invalid_reset_link'], 400)
        finally:
            if token:
                RedisUtil.delete_key(loaded_data['reset_id'])

        user = User.query.get(token_data['id'])
        user.password = loaded_data['password']
        user.update()
        return {'status': 'success', 'message': PASSWORD_CHANGED}
