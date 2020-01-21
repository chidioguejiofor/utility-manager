from api.utils.success_messages import RETRIEVED
from api.utils.error_messages import authentication_errors
from api.models import Membership
from tests.mocks.user import UserGenerator

from tests.assertions import assert_paginator_meta

import json
import math

ORG_INVITATION_URL = '/api/org/{}/invitations'
USER_INVITATION_URL = '/api/user/invitations'

INVITE_KEY = 'invites'


class TestRetrieveUserInvitations:
    def test_should_retrieve_user_invitations_when_user_is_verified(
            self, init_db, client, saved_user_invitations):
        org_objs, user, org_ids, invitations, regular_user_id = saved_user_invitations(
            5)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.get(USER_INVITATION_URL,
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Invitations')
        assert response_body['status'] == 'success'
        for data in response_body['data']:
            assert data['organisation']['id'] in org_ids
            assert data['role']['id'] == regular_user_id
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(invitations),
            max_objects_per_page=10,
            total_pages=math.ceil(len(invitations) / 10),
            next_page=None,
            prev_page=None,
        )

    def test_user_should_be_able_to_paginate_data(self, init_db, client,
                                                  saved_user_invitations):
        total_invitations = 15
        page_num = 2
        page_limit = 5
        org_objs, user, org_ids, invitations, regular_user_id = saved_user_invitations(
            total_invitations)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)

        response = client.get(
            f'{USER_INVITATION_URL}?page={page_num}&page_limit={page_limit}',
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Invitations')
        assert response_body['status'] == 'success'
        for data in response_body['data']:
            assert data['organisation']['id'] in org_ids
            assert data['role']['id'] == regular_user_id

        assert_paginator_meta(
            response_body,
            current_page=page_num,
            total_objects=total_invitations,
            max_objects_per_page=page_limit,
            total_pages=math.ceil(total_invitations / page_limit),
            next_page=page_num + 1,
            prev_page=page_num - 1,
        )


class TestRetrieveOrganisationInvitations:
    def test_should_retrieve_organisation_invitations_when_user_is_verified(
            self, init_db, client, saved_organisation_invitations):
        user_objs, org, user_ids, invitations, regular_user_id = saved_organisation_invitations(
            5)
        token = UserGenerator.generate_token(org.creator)
        client.set_cookie('/', 'token', token)
        response = client.get(ORG_INVITATION_URL.format(org.id),
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Invitations')
        assert response_body['status'] == 'success'
        for data in response_body['data']:
            assert 'organisation' not in data
            assert data['role']['id'] == regular_user_id
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(invitations),
            max_objects_per_page=10,
            total_pages=math.ceil(len(invitations) / 10),
            next_page=None,
            prev_page=None,
        )

    def test_admin_should_be_able_to_paginate_data(
            self, init_db, client, saved_organisation_invitations):
        total_invitations = 15
        page_num = 2
        page_limit = 5
        user_objs, org, user_ids, invitations, regular_user_id = saved_organisation_invitations(
            total_invitations)
        token = UserGenerator.generate_token(org.creator)
        client.set_cookie('/', 'token', token)

        response = client.get(
            f'{ORG_INVITATION_URL.format(org.id)}?page={page_num}&page_limit={page_limit}',
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Invitations')
        assert response_body['status'] == 'success'
        for data in response_body['data']:
            assert 'organisation' not in data
            assert data['role']['id'] == regular_user_id

        assert_paginator_meta(
            response_body,
            current_page=page_num,
            total_objects=total_invitations,
            max_objects_per_page=page_limit,
            total_pages=math.ceil(total_invitations / page_limit),
            next_page=page_num + 1,
            prev_page=page_num - 1,
        )

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