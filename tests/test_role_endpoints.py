import math
import json
from api.models import Role
from api.utils.success_messages import RETRIEVED
from .mocks.user import UserGenerator
from .assertions import assert_paginator_meta

RETRIEVE_ROLE_ENDPOINT = '/api/org/{}/roles'


class TestRetrieveRole:
    def test_should_retrieve_roles_info(self, init_db, client,
                                        saved_org_and_user_generator):
        roles = Role.query.all()
        user, org = saved_org_and_user_generator
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.get(RETRIEVE_ROLE_ENDPOINT.format(org.id),
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Roles')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(roles),
            max_objects_per_page=10,
            total_pages=math.ceil(len(roles) / 10),
            next_page=None,
            prev_page=None,
        )

    def test_should_be_able_to_specify_pagination_data(
            self, init_db, client, saved_org_and_user_generator):
        roles = Role.query.all()
        user, org = saved_org_and_user_generator
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        page_limit = 1
        page = 2
        response = client.get(
            f'{RETRIEVE_ROLE_ENDPOINT.format(org.id)}?page={page}&page_limit={page_limit}',
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Roles')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=page,
            total_objects=len(roles),
            max_objects_per_page=page_limit,
            total_pages=math.ceil(len(roles) / page_limit),
            next_page=page + 1,
            prev_page=page - 1,
        )

    def test_should_be_able_to_search_for_admin_role_easily(
            self, init_db, client, saved_org_and_user_generator):
        admin_role_name = 'ADMIN'
        roles = Role.query.filter(Role.name.ilike(admin_role_name)).all()
        admin_role = roles[0]
        user, org = saved_org_and_user_generator
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{RETRIEVE_ROLE_ENDPOINT.format(org.id)}?name_search={admin_role_name}',
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Roles')
        assert response_body['status'] == 'success'

        assert response_body['data'][0]['name'] == admin_role.name
        assert response_body['data'][0][
            'description'] == admin_role.description
        assert response_body['data'][0]['id'] == admin_role.id
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(roles),
            max_objects_per_page=10,
            total_pages=math.ceil(len(roles) / 10),
            next_page=None,
            prev_page=None,
        )
