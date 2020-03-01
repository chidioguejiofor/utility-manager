from .base import BaseOrgView, BasePaginatedView
from settings import endpoint
from api.schemas import RoleSchema
from api.models import Role
from api.utils.success_messages import RETRIEVED


@endpoint('/org/<string:org_id>/roles')
class OrgRoleView(BaseOrgView, BasePaginatedView):
    __model__ = Role
    PROTECTED_METHODS = ['GET']
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }
    __SCHEMA__ = RoleSchema
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Roles')
    SORT_KWARGS = {'defaults': 'name', 'sort_fields': {'name'}}

    def filter_get_method_query(self, query, **kwargs):
        return query
