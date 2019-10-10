import jwt
from .base import BaseView
from settings import endpoint
from flask import request

from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.models import User
from api.schemas import ResetPasswordSchema
from api.utils.success_messages import RESET_PASS_MAIL, PASSWORD_CHANGED
from api.utils.constants import RESET_TOKEN, RESET_PASSWORD_SUBJECT


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
        password = request.get_json().get('password')
        if not password:
            raise MessageOnlyResponseException(
                serialization_error['pass_is_required'], 400)
        auth = request.headers.get('Authorization')
        token_data = TokenValidator.decode_from_auth_header(auth, RESET_TOKEN)

        user = User.query.get(token_data['id'])
        user.password = password
        user.update()
        return {'status': 'success', 'message': PASSWORD_CHANGED}
