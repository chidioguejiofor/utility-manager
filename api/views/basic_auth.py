import jwt
from .base import BaseView, CookieGeneratorMixin
from settings import endpoint
from flask import request, redirect, make_response

from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.success_messages import REG_VERIFIED, CONFIRM_EMAIL_RESENT
from api.utils.exceptions import ResponseException
from api.utils.token_validator import TokenValidator
from api.models import User
from api.schemas import UserSchema, LoginSchema
from api.utils.success_messages import CREATED, LOGIN
from api.utils.constants import CONFIRM_TOKEN
from api.services.redis_util import RedisUtil


@endpoint('/auth/register')
class Register(BaseView, CookieGeneratorMixin):
    def post(self):
        user_obj = UserSchema().load(request.get_json())
        user_obj.save()
        user_data = UserSchema().dump_success_data(user_obj,
                                                   CREATED.format('user'))
        return user_data, 201


@endpoint('/auth/resend-email')
class ResendEmail(BaseView):
    protected_methods = ['POST']
    unverified_methods = ['POST']

    def post(self, user_data):
        from api.utils.emails import EmailUtil
        redirect_url = request.get_json().get('redirectURL')
        if not redirect_url or not ('http://' in redirect_url
                                    or 'https://' in redirect_url):
            raise ResponseException(
                serialization_error['invalid_url'].format('Redirect URL'),
                status_code=400,
            )
        user = User.query.get(user_data['id'])
        user.redirect_url = redirect_url
        if user.verified:
            raise ResponseException(
                serialization_error['already_verified'],
                status_code=400,
            )

        EmailUtil.send_verification_email_to_user(user)

        return {
            'status': 'success',
            'message': CONFIRM_EMAIL_RESENT.format(user.email)
        }, 200


@endpoint('/auth/confirm/<string:confirm_id>')
class ConfirmEmail(BaseView, CookieGeneratorMixin):
    def get(self, **kwargs):
        token = RedisUtil.get_key(kwargs.get('confirm_id'))
        user = None
        try:
            token_data = TokenValidator.decode_token_data(token, CONFIRM_TOKEN)
            user = User.query.get(token_data['id'])
            user.verified = True
            user.update()

            redirect_url = f"{token_data['redirect_url']}?success=true&message={REG_VERIFIED}"
            RedisUtil.delete_key((kwargs.get('confirm_id')))
        except jwt.exceptions.ExpiredSignatureError:
            token_data = TokenValidator.decode_token_data(token,
                                                          CONFIRM_TOKEN,
                                                          verify=False)
            message = authentication_errors['confirmation_expired']
            redirect_url = f"{token_data['redirect_url']}?success=false&message={message}"
            RedisUtil.delete_key((kwargs.get('confirm_id')))
        except Exception:
            raise ResponseException(
                serialization_error['invalid_confirmation_link'], 404)

        resp = redirect(redirect_url, code=302)
        if user:

            resp = self.generate_cookie(resp, user)
        return resp


@endpoint('/auth/login')
class Login(BaseView, CookieGeneratorMixin):
    def post(self):
        user_data = LoginSchema().load(request.get_json())
        username_or_email = user_data['username_or_email']
        password = user_data['password']
        query_by_email = '@' in username_or_email
        if query_by_email:
            user = User.query.filter_by(email=username_or_email).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()

        if user and user.verify_password(password):
            user_json = UserSchema().dump_success_data(user,
                                                       LOGIN.format('user'))
            resp = make_response(user_json)
            resp.status_code = 200
            return self.generate_cookie(resp, user)

        raise ResponseException(
            message=serialization_error['login_failed'],
            status_code=400,
        )

    def delete(self):
        resp = make_response({
            'status': 'success',
            'data': 'User was logged out successfully'
        })
        resp.status_code = 200
        return self.generate_cookie(resp, None)
