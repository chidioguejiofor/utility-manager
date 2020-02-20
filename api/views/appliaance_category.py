from .base import BaseOrgView
from settings import org_endpoint
from flask import request
from api.schemas import ApplianceCategory
from api.utils.success_messages import CREATED
from api.utils.exceptions import ResponseException


@org_endpoint('/appliance-category')
class ApplianceCategoryView(BaseOrgView):
    protected_methods = ['POST']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    def post(self, org_id, user_data, membership):
        json_data = request.get_json()
        json_data = json_data if json_data else {}
        json_data['organisationId'] = org_id
        json_data['created_by_id'] = user_data['id']
        category_obj = ApplianceCategory().load(json_data)
        category_obj.save()
        res_data = ApplianceCategory().dump_success_data(
            category_obj, CREATED.format('Appliance Category'))
        return res_data, 201
