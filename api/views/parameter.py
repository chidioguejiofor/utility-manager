from settings import org_endpoint
from flask import request
from .base import BaseOrgView, BasePaginatedView
from api.models import Parameter
from api.schemas import ParameterSchema
from api.utils.success_messages import CREATED, RETRIEVED


@org_endpoint('/parameters')
class ParameterView(BaseOrgView, BasePaginatedView):
    __model__ = Parameter
    __SCHEMA__ = ParameterSchema
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Parameter')
    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER']}
    PROTECTED_METHODS = ['POST', 'GET']
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
        'unit.name': {
            'filter_type': 'ilike'
        },
    }
    SORT_KWARGS = {
        'defaults': 'created_at,name',
        'sort_fields': {'created_at', 'name'}
    }
    SCHEMA_EXCLUDE = [
        'created_by_id', 'updated_by', 'updated_by_id', 'organisation_id'
    ]
    EAGER_LOADING_FIELDS = ['unit', 'created_by']

    def post(self, org_id, user_data, membership):
        exclude_fields = ['created_by', 'updated_by', 'organisation_id']
        json_data = request.get_json()
        json_data['organisationId'] = org_id
        json_data['createdById'] = user_data['id']
        param_obj = ParameterSchema().load(json_data)
        param_obj.save()
        res_data = ParameterSchema(exclude=exclude_fields).dump_success_data(
            param_obj, CREATED.format('Parameter'))
        return res_data, 201
