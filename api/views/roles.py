from .base import BaseView, FilterByQueryMixin
from settings import endpoint
from flask import request
from api.schemas import RoleSchema
from api.models import Membership, Role
from api.utils.exceptions import ResponseException
from api.utils.success_messages import RETRIEVED
from api.utils.error_messages import serialization_error


@endpoint('/org/<string:org_id>/roles')
class OrgRoleView(BaseView, FilterByQueryMixin):
    __model__ = Role
    protected_methods = ['GET']
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {'defaults': 'name', 'sort_fields': {'name'}}

    def get(self, user_data, org_id):
        membership = Membership.query.options().filter_by(
            organisation_id=org_id, user_id=user_data['id']).first()

        if not membership:
            raise ResponseException(
                message=serialization_error['not_found'].format(
                    'Organisation id'),
                status_code=404,
            )
        query_params = request.args
        query = self.search_model(query_params)
        page_query, meta = self.paginate_query(query, query_params)
        data = RoleSchema(many=True).dump_success_data(
            page_query, message=RETRIEVED.format('Roles'))
        data['meta'] = meta
        return data, 200
