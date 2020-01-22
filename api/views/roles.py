from .base import BaseView, BasePaginatedView
from settings import endpoint
from api.schemas import RoleSchema
from api.models import Membership, Role
from api.utils.exceptions import ResponseException
from api.utils.success_messages import RETRIEVED
from api.utils.error_messages import serialization_error


@endpoint('/org/<string:org_id>/roles')
class OrgRoleView(BaseView, BasePaginatedView):
    __model__ = Role
    protected_methods = ['GET']
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }
    __SCHEMA__ = RoleSchema
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Roles')
    SORT_KWARGS = {'defaults': 'name', 'sort_fields': {'name'}}

    def filter_get_method_query(self, query, **kwargs):
        user_data = kwargs.get('user_data')
        org_id = kwargs.get('org_id')
        membership = Membership.query.options().filter_by(
            organisation_id=org_id, user_id=user_data['id']).first()

        if not membership:
            raise ResponseException(
                message=serialization_error['not_found'].format(
                    'Organisation id'),
                status_code=404,
            )
        return super().filter_get_method_query(query)
