from .base import BaseView, FilterByQueryMixin
from settings import endpoint
from flask import request
from api.schemas import OrganisationSchema, OrgAndMembershipSchema, InvitationRequestSchema, InvitationSchema
from api.models import Membership, Invitation
from api.utils.exceptions import ResponseException
from api.utils.success_messages import CREATED, RETRIEVED, INVITING_USER_MSG_DICT
from api.utils.error_messages import invitation_errors
from api.services.redis_util import RedisUtil
from sqlalchemy import exc, orm


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
class RetrieveUserMemberships(BaseView, FilterByQueryMixin):
    __model__ = Membership
    SORT_KWARGS = {'defaults': 'role_id', 'sort_fields': {'role_id'}}
    protected_methods = ['GET']
    unverified_methods = ['GET']

    def get(self, user_data):
        memberships = Membership.query.filter_by(user_id=user_data['id'])
        query_params = request.args
        page_query, meta = self.paginate_query(memberships, query_params)
        data = OrgAndMembershipSchema(many=True).dump_success_data(
            page_query, message=RETRIEVED.format('organisations'))
        data['meta'] = meta
        return data, 200
