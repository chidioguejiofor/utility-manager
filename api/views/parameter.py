from .base import BaseView
from settings import endpoint
from flask import request
from api.models import Membership, RoleEnum
from api.schemas import ParameterSchema
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.success_messages import CREATED
from api.utils.error_messages import serialization_error, authentication_errors


@endpoint('/org/<string:org_id>/parameters')
class CreateParameter(BaseView):
    protected_methods = ['POST']

    def post(self, org_id, user_data):
        json_data = request.get_json()
        user_org_membership = Membership.query.filter(
            (Membership.user_id == user_data['id'])
            & (Membership.organisation_id == org_id)).first()
        if not user_org_membership:
            raise MessageOnlyResponseException(
                message=serialization_error['not_found'].format(
                    'Organisation'),
                status_code=404,
            )
        if user_org_membership.role not in [RoleEnum.MANAGER, RoleEnum.OWNER]:
            raise MessageOnlyResponseException(
                message=authentication_errors['forbidden'].format(
                    'create a parameter'),
                status_code=403,
            )
        json_data['organisationId'] = org_id
        json_data['createdById'] = user_data['id']
        param_obj = ParameterSchema().load(json_data)
        param_obj.save()
        res_data = ParameterSchema().dump_success_data(
            param_obj, CREATED.format('Parameter'))
        return res_data, 201
