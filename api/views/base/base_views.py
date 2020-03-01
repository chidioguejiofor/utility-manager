from .base_queries import PaginatorMixin, SearchFilterMixin
import os
from flask_restplus import Resource
from flask import request
from api.utils.token_validator import TokenValidator
from api.utils.constants import LOGIN_TOKEN
from datetime import timedelta, datetime
from .decoratorators import Authentication, OrgViewDecorator
from api.services.redis_util import RedisUtil
from api.utils.constants import COOKIE_TOKEN_KEY, REDIS_TOKEN_HASH_KEY
from api.utils.id_generator import IDGenerator


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class BaseView(Resource):
    PROTECTED_METHODS = []
    unverified_methods = []

    @classproperty
    def method_decorators(self):
        return [Authentication(self)]


class BaseOrgView(BaseView):
    ALLOWED_ROLES = {}

    @classproperty
    def method_decorators(self):
        return [OrgViewDecorator(self), Authentication(self)]

    def filter_get_method_query(self, query, *args, org_id, **kwargs):
        return query.filter((self.__model__.organisation_id == org_id)
                            | (self.__model__.organisation_id.is_(None)))


class BasePaginatedView(SearchFilterMixin, PaginatorMixin):
    __SCHEMA__ = None
    RETRIEVE_SUCCESS_MSG = None
    SCHEMA_EXCLUDE = []
    EAGER_LOADING_FIELDS = []

    def get(self, *args, **kwargs):
        self._joined_fields = []  # used in BaseFilterMixin
        query_params = request.args
        query = self.search_model(query_params)
        query = self.filter_get_method_query(query, *args, **kwargs)
        page_query, meta = self.paginate_query(query, query_params)
        data = self.__SCHEMA__(exclude=self.SCHEMA_EXCLUDE,
                               many=True).dump_success_data(
                                   page_query,
                                   message=self.RETRIEVE_SUCCESS_MSG)
        data['meta'] = meta
        return data, 200

    def filter_get_method_query(self, query, *args, **kwargs):
        return query


class CookieGeneratorMixin:
    def generate_cookie(self, resp, user):
        """Adds cookie to the response

           When user is None, it invalidates the previously sent token
           Args:
               resp flask.Response: response object from
               user models.User: User model object that would be used to generate token
               expired bool: when True, token would be expired

           Returns:
               flask.Response: final response object would have the required cookie

       """
        secure_flag = os.getenv('FLASK_ENV') == 'production'
        cookie_value = 'deleted'
        expires = datetime.now() - timedelta(days=100)
        if user:
            payload = {
                'type': LOGIN_TOKEN,
                'email': user.email,
                'id': user.id,
                'username': user.username,
                "verified": user.verified,
            }
            expires_in = timedelta(days=5)
            token = TokenValidator.create_token(payload)
            token_id = IDGenerator.generate_id()
            redis_hash = f'{user.id}_{REDIS_TOKEN_HASH_KEY}'
            RedisUtil.hset(redis_hash, token_id, token, expires_in)
            cookie_value = f'{user.id}/{token_id}'
            expires = datetime.now() + expires_in

        resp.set_cookie(COOKIE_TOKEN_KEY,
                        cookie_value,
                        path='/',
                        httponly=True,
                        secure=secure_flag,
                        expires=expires)
        return resp
