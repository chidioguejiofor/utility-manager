import jwt
from .base import BaseView, CookieGeneratorMixin
from settings import endpoint
from flask import request, redirect

from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.success_messages import REG_VERIFIED, CONFIRM_EMAIL_RESENT
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.token_validator import TokenValidator
from api.models import User
from api.schemas import UserSchema
from api.utils.success_messages import CREATED, LOGIN
from api.utils.constants import CONFIRM_TOKEN


@endpoint('/auth/register')
class Register(BaseView, CookieGeneratorMixin):
    def post(self):
        user_obj = UserSchema().load(request.get_json())
        user_obj.save()
        user_data = UserSchema().dump_success_data(user_obj,
                                                   CREATED.format('user'))
        headers = self.generate_cookie_header(user_data['data'])
        return user_data, 201, headers


@endpoint('/auth/resend-email')
class ResendEmail(BaseView):
    def post(self):
        from api.utils.emails import EmailUtil
        user_data = self.decode_token()
        redirect_url = request.get_json().get('redirectURL')
        if not redirect_url or not ('http://' in redirect_url
                                    or 'https://' in redirect_url):
            raise MessageOnlyResponseException(
                serialization_error['invalid_url'].format('Redirect URL'),
                status_code=400,
            )
        user = User.query.get(user_data['id'])
        user.redirect_url = redirect_url
        if user.verified:
            raise MessageOnlyResponseException(
                serialization_error['already_verified'],
                status_code=400,
            )

        EmailUtil.send_verification_email_to_user(user)

        return {
            'status': 'success',
            'message': CONFIRM_EMAIL_RESENT.format(user.email)
        }, 200


@endpoint('/auth/confirm/<string:token>')
class ConfirmEmail(BaseView):
    @staticmethod
    def get(**kwargs):
        try:
            token_data = TokenValidator.decode_token_data(
                kwargs.get('token'), CONFIRM_TOKEN)
            user = User.query.get(token_data['id'])
            user.verified = True
            User.update()
            redirect_url = f"{token_data['redirect_url']}?success=true&message={REG_VERIFIED}"
        except jwt.exceptions.ExpiredSignatureError:
            token_data = TokenValidator.decode_token_data(kwargs.get('token'),
                                                          CONFIRM_TOKEN,
                                                          verify=False)
            message = authentication_errors['confirmation_expired']
            redirect_url = f"{token_data['redirect_url']}?success=false&message={message}"
        except Exception:
            raise MessageOnlyResponseException(
                serialization_error['invalid_confirmation_link'], 404)

        return redirect(redirect_url, code=302)


@endpoint('/auth/login')
class Login(BaseView, CookieGeneratorMixin):
    def post(self):
        user_data = request.get_json()
        username_or_email = user_data.get('usernameOrEmail')
        password = user_data.get('password')

        query_by_email = '@' in username_or_email
        if query_by_email:
            user = User.query.filter_by(email=username_or_email).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()

        if user and user.verify_password(password):
            user_json = UserSchema().dump_success_data(user,
                                                       LOGIN.format('user'))
            headers = self.generate_cookie_header(user_json['data'])
            return user_json, 200, headers

        raise MessageOnlyResponseException(
            message=serialization_error['login_failed'],
            status_code=400,
        )

    def delete(self):
        headers = self.generate_cookie_header(expired=True)
        data = {
            'status': 'success',
            'data': 'User was logged out successfully'
        }
        return data, 200, headers
