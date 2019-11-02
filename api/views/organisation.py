from .base import BaseView, FilterByQueryMixin
from settings import endpoint
from flask import request
from api.utils.exceptions import MessageOnlyResponseException
from api.schemas import OrganisationSchema, OrgAndMembershipSchema
from api.models import Membership
from api.utils.success_messages import CREATED, RETRIEVED


@endpoint('/org/create')
class CreateOrg(BaseView):
    def post(self):
        user_data = self.decode_token(check_user_is_verified=True)
        logo = request.files.get('logo')
        data_dict = {**request.form, 'logo': logo}
        org_obj = OrganisationSchema().load(data_dict)

        org_obj.creator_id = user_data['id']
        org_obj.filename = f'dumped_files/{user_data["id"]}-organisation.jpg'
        org_obj.logo.save(dst=org_obj.filename)
        org_obj.save()
        org_data = OrganisationSchema().dump_success_data(
            org_obj, CREATED.format('organisation'))
        return org_data, 201


@endpoint('/user/orgs')
class RetrieveUserMemberships(BaseView, FilterByQueryMixin):
    __model__ = Membership
    SORT_KWARGS = {'defaults': 'role', 'sort_fields': {'role'}}

    def get(self):
        user_data = self.decode_token()
        memberships = Membership.query.filter_by(user_id=user_data['id'])
        query_params = request.args
        page_query, meta = self.paginate_query(memberships, query_params)
        data = OrgAndMembershipSchema(many=True).dump_success_data(
            page_query, message=RETRIEVED.format('organisations'))
        data['meta'] = meta
        return data, 200
