from .base import BaseView, BaseOrgView
from settings import endpoint
from flask import request
from api.models import Membership
from api.services.redis_util import RedisUtil
from api.schemas import ParameterSchema
from api.utils.exceptions import ResponseException
from api.utils.success_messages import CREATED
from api.utils.error_messages import serialization_error, authentication_errors


@endpoint('/org/<string:org_id>/parameters')
class CreateParameter(BaseOrgView):
    protected_methods = ['POST']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER']}

    def post(self, org_id, user_data, membership):
        json_data = request.get_json()
        json_data['organisationId'] = org_id
        json_data['createdById'] = user_data['id']
        param_obj = ParameterSchema().load(json_data)
        param_obj.save()
        res_data = ParameterSchema().dump_success_data(
            param_obj, CREATED.format('Parameter'))
        return res_data, 201
