from .base import BaseView, BasePaginatedView
from settings import endpoint
from flask import request
from api.schemas import OrganisationSchema, OrgAndMembershipSchema
from api.models import Membership
from api.utils.success_messages import CREATED, RETRIEVED


@endpoint('/org/create')
class CreateOrg(BaseView):
    protected_methods = ['POST']

    def post(self, user_data):
        logo = request.files.get('logo')
        data_dict = {**request.form, 'logo': logo}
        org_obj = OrganisationSchema().load(data_dict)

        org_obj.creator_id = user_data['id']
        org_obj.save(commit=False)
        org_data = OrganisationSchema().dump_success_data(
            org_obj, CREATED.format('organisation'))
        return org_data, 201


@endpoint('/user/orgs')
class RetrieveUserMemberships(BaseView, BasePaginatedView):
    __model__ = Membership
    protected_methods = ['GET']
    unverified_methods = ['GET']

    SORT_KWARGS = {
        'defaults': 'organisation.name',
        'sort_fields': {'organisation.name', 'role_id', 'role.name'}
    }
    SEARCH_FILTER_ARGS = {
        'role_id': {
            'filter_type': 'eq'
        },
        'role.name': {
            'filter_type': 'ilike'
        },
    }
    __SCHEMA__ = OrgAndMembershipSchema
    EAGER_LOADING_FIELDS = ['organisation', 'role']
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('organisations')

    def filter_get_method_query(self, query, **kwargs):
        user_data = kwargs.get('user_data')
        return query.filter(Membership.user_id == user_data['id'])
