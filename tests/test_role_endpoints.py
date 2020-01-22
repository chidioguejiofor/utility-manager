import math
from api.models import Role
from api.utils.success_messages import RETRIEVED
from .mocks.user import UserGenerator
from .assertions import assert_paginator_data_values

RETRIEVE_ROLE_ENDPOINT = '/api/org/{}/roles'


class TestRetrieveRole:
    def create_test_precondition(self, saved_org_and_user_generator):
        roles = Role.query.all()
        user, org = saved_org_and_user_generator
        token = UserGenerator.generate_token(user)
        return token, roles, user, org

    def test_should_retrieve_roles_info(self, init_db, client,
                                        saved_org_and_user_generator):
        token, roles, user, org = self.create_test_precondition(
            saved_org_and_user_generator)
        assert_paginator_data_values(
            created_objs=roles,
            client=client,
            token=token,
            url=RETRIEVE_ROLE_ENDPOINT.format(org.id),
            success_msg=RETRIEVED.format('Roles'),
            next_page=None,
            prev_page=None,
        )

    def test_should_be_able_to_specify_pagination_data(
            self, init_db, client, saved_org_and_user_generator):
        token, roles, user, org = self.create_test_precondition(
            saved_org_and_user_generator)
        page_limit = 1
        page = 2
        assert_paginator_data_values(
            created_objs=roles,
            client=client,
            token=token,
            url=
            f'{RETRIEVE_ROLE_ENDPOINT.format(org.id)}?page={page}&page_limit={page_limit}',
            success_msg=RETRIEVED.format('Roles'),
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
        user, org = saved_org_and_user_generator
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response_body = assert_paginator_data_values(
            created_objs=roles,
            client=client,
            token=token,
            url=
            f'{RETRIEVE_ROLE_ENDPOINT.format(org.id)}?name_search={admin_role_name}',
            success_msg=RETRIEVED.format('Roles'),
            current_page=1,
            total_objects=len(roles),
            max_objects_per_page=10,
            total_pages=math.ceil(len(roles) / 10),
            next_page=None,
            prev_page=None,
        )

        admin_role = roles[0]
        assert response_body['data'][0]['name'] == admin_role.name
        assert response_body['data'][0][
            'description'] == admin_role.description
        assert response_body['data'][0]['id'] == admin_role.id
