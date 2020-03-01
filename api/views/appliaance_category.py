from .base import BaseOrgView, BasePaginatedView
from api.models import ApplianceCategory
from settings import org_endpoint
from flask import request
from api.schemas import ApplianceCategorySchema
from api.utils.success_messages import CREATED, RETRIEVED


@org_endpoint('/appliance-category')
class ApplianceCategoryView(BaseOrgView, BasePaginatedView):
    __SCHEMA__ = ApplianceCategorySchema
    __model__ = ApplianceCategory
    PROTECTED_METHODS = ['POST', 'GET']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    # query settings
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': 'created_at',
        'sort_fields': {'created_at', 'name'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Appliance Category')
    SCHEMA_EXCLUDE = ['organisation_id']

    def post(self, org_id, user_data, membership):
        json_data = request.get_json()
        json_data = json_data if json_data else {}
        json_data['organisation_id'] = org_id
        json_data['created_by_id'] = user_data['id']
        category_obj = ApplianceCategorySchema().load(json_data)
        category_obj.save()
        res_data = ApplianceCategorySchema().dump_success_data(
            category_obj, CREATED.format('Appliance Category'))
        return res_data, 201
