from .base import BaseView
from settings import endpoint
from flask import request

from api.schemas import OrganisationSchema
from api.utils.success_messages import CREATED


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
        print(org_data)
        return org_data, 201
