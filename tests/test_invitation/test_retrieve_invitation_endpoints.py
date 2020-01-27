from api.utils.success_messages import RETRIEVED
from api.utils.error_messages import authentication_errors
from api.models import Membership, Organisation, db
from tests.mocks.user import UserGenerator
from tests.assertions import assert_paginator_data_values

import json
import math

ORG_INVITATION_URL = '/api/org/{}/invitations'
USER_INVITATION_URL = '/api/user/invitations'
INVITE_KEY = 'invites'


def run_test_precondition():
    Membership.query.delete()
    Organisation.query.delete()
    db.session.commit()


class TestRetrieveUserInvitations:
    def test_should_retrieve_user_invitations_when_user_is_verified(
            self, init_db, client, saved_user_invitations):
        run_test_precondition()
        org_objs, user, org_ids, invitations, regular_user_id = saved_user_invitations(
            5)
        token = UserGenerator.generate_token(user)
        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=USER_INVITATION_URL,
            success_msg=RETRIEVED.format('Invitations'),
            current_page=1,
            next_page=None,
            prev_page=None,
        )
        for data in response_body['data']:
            assert data['organisation']['id'] in org_ids
            assert data['role']['id'] == regular_user_id

    def test_should_be_able_to_search_role_name(self, init_db, client,
                                                saved_user_invitations):
        run_test_precondition()
        _, user, _, _, _ = saved_user_invitations(5)
        org_objs, user, org_ids, invitations, regular_user_id = saved_user_invitations(
            5, 'ADMIN', user=user)

        token = UserGenerator.generate_token(user)

        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=f'{USER_INVITATION_URL}?role.name_search=ADMIN',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=1,
            total_objects=5,
            next_page=None,
            prev_page=None,
        )
        for data in response_body['data']:
            assert data['role']['name'] == 'ADMIN'
            assert data['organisation']['id'] in org_ids

    def test_should_perform_an_exact_match_when_searching_by_role_id(
            self, init_db, client, saved_user_invitations):
        run_test_precondition()
        _, user, _, _, regular_user_id = saved_user_invitations(5)
        org_objs, user, org_ids, invitations, admin_role_id = saved_user_invitations(
            5, 'ADMIN', user=user)

        token = UserGenerator.generate_token(user)

        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=f'{USER_INVITATION_URL}?role_id_search={admin_role_id}',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=1,
            total_objects=5,
            next_page=None,
            prev_page=None,
        )

        excluding_last_letter = regular_user_id[0:-1]
        response_body_2 = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=f'{USER_INVITATION_URL}?role_id_search={excluding_last_letter}',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=1,
            total_pages=0,
            total_objects=0,
            next_page=None,
            prev_page=None,
        )

        for data in response_body['data']:
            assert data['role']['name'] == 'ADMIN'
            assert data['organisation']['id'] in org_ids

        assert len(response_body_2['data']) == 0

    def test_should_be_able_to_sort_by_role_name(self, init_db, client,
                                                 saved_user_invitations):
        run_test_precondition()
        _, user, _, _, regular_user_id = saved_user_invitations(5)
        org_objs, user, org_ids, invitations, admin_role_id = saved_user_invitations(
            5, 'ADMIN', user=user)

        token = UserGenerator.generate_token(user)

        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=f'{USER_INVITATION_URL}?sort_by=+role.name',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=1,
            total_objects=10,
            next_page=None,
            prev_page=None,
        )

        response_body_two = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=f'{USER_INVITATION_URL}?sort_by=-role.name',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=1,
            total_objects=10,
            next_page=None,
            prev_page=None,
        )
        assert len(response_body['data']) == 10

        first_five = response_body['data'][0:5]
        last_five = response_body['data'][5:]

        for admin_inv in first_five:
            assert admin_inv['role']['name'] == 'ADMIN'
        for regular_inv in last_five:
            assert regular_inv['role']['name'] == 'REGULAR USERS'

        # This is inverted
        first_five_two = response_body_two['data'][0:5]
        last_five_two = response_body_two['data'][5:]

        for regular_inv in last_five_two:
            assert regular_inv['role']['name'] == 'ADMIN'

        for admin_inv in first_five_two:
            assert admin_inv['role']['name'] == 'REGULAR USERS'

    def test_user_should_be_able_to_paginate_data(self, init_db, client,
                                                  saved_user_invitations):
        run_test_precondition()
        total_invitations = 15
        page_num = 2
        page_limit = 5
        org_objs, user, org_ids, invitations, regular_user_id = saved_user_invitations(
            total_invitations)
        token = UserGenerator.generate_token(user)
        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=
            f'{USER_INVITATION_URL}?page={page_num}&page_limit={page_limit}',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=page_num,
            total_objects=total_invitations,
            max_objects_per_page=page_limit,
            total_pages=math.ceil(total_invitations / page_limit),
            next_page=page_num + 1,
            prev_page=page_num - 1,
        )

        for data in response_body['data']:
            assert data['organisation']['id'] in org_ids
            assert data['role']['id'] == regular_user_id


class TestRetrieveOrganisationInvitations:
    def test_should_retrieve_organisation_invitations_when_user_is_verified(
            self, init_db, client, saved_organisation_invitations):
        user_objs, org, user_ids, invitations, regular_user_id = saved_organisation_invitations(
            5)
        token = UserGenerator.generate_token(org.creator)
        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=ORG_INVITATION_URL.format(org.id),
            success_msg=RETRIEVED.format('Invitations'),
            next_page=None,
            prev_page=None,
        )
        for data in response_body['data']:
            assert 'organisation' not in data
            assert data['role']['id'] == regular_user_id

    def test_admin_should_be_able_to_paginate_data(
            self, init_db, client, saved_organisation_invitations):
        total_invitations = 15
        page_num = 2
        page_limit = 5
        user_objs, org, user_ids, invitations, regular_user_id = saved_organisation_invitations(
            total_invitations)
        token = UserGenerator.generate_token(org.creator)
        response_body = assert_paginator_data_values(
            created_objs=invitations,
            client=client,
            token=token,
            url=
            f'{ORG_INVITATION_URL.format(org.id)}?page={page_num}&page_limit={page_limit}',
            success_msg=RETRIEVED.format('Invitations'),
            current_page=page_num,
            next_page=page_num + 1,
            prev_page=page_num - 1,
            total_objects=total_invitations,
            max_objects_per_page=page_limit,
            total_pages=math.ceil(total_invitations / page_limit),
        )

        for data in response_body['data']:
            assert 'organisation' not in data
            assert data['role']['id'] == regular_user_id

    def test_should_fail_when_the_user_is_not_an_admin_in_the_organisation(
            self, init_db, client, saved_organisation_invitations):
        total_invitations = 5
        page_num = 2
        page_limit = 5
        user_objs, org, user_ids, invitations, regular_user_id = saved_organisation_invitations(
            total_invitations)
        regular_user = UserGenerator.generate_model_obj(save=True,
                                                        verified=True)
        Membership(
            organisation_id=org.id,
            user_id=regular_user.id,
            role_id=regular_user_id,
        ).save(commit=True)

        token = UserGenerator.generate_token(regular_user)
        client.set_cookie('/', 'token', token)

        response = client.get(
            f'{ORG_INVITATION_URL.format(org.id)}?page={page_num}&page_limit={page_limit}',
            content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 403
        assert response_body['message'] == authentication_errors[
            'forbidden'].format('access this')
