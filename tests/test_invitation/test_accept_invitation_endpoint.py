from api.utils.success_messages import ADDED_TO_ORG
from api.utils.error_messages import authentication_errors, serialization_error
from api.models import Membership
from tests.mocks.user import UserGenerator

from tests.assertions import assert_paginator_meta

import json
import math

USER_INVITATION_URL = '/api/user/invitations/{}/accept'

INVITE_KEY = 'invites'


class TestUserAcceptInvitation:
    def test_user_should_be_able_to_accept_invitation(self, init_db, client,
                                                      saved_user_invitations):
        org_objs, user, org_ids, invitations, regular_user_id = \
            saved_user_invitations(1)

        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.post(USER_INVITATION_URL.format(invitations[0].id),
                               content_type="application/json")
        response_body = json.loads(response.data)
        member_id = Membership.query.filter_by(
            user_id=user.id,
            organisation_id=invitations[0].organisation_id,
        ).first().id
        assert response.status_code == 201
        assert response_body['status'] == 'success'
        assert response_body['data']['id'] == member_id
        assert response_body['data']['organisationId'] == org_objs[0].id
        assert response_body['data']['roleId'] == regular_user_id
        assert response_body['message'] == ADDED_TO_ORG

    def test_should_fail_when_user_was_not_sent_invite(self, init_db, client,
                                                       saved_user_invitations):
        org_objs, user, org_ids, invitations, regular_user_id = \
            saved_user_invitations(1)

        unknown_user = UserGenerator.generate_model_obj(save=True,
                                                        verified=True)
        token = UserGenerator.generate_token(unknown_user)
        client.set_cookie('/', 'token', token)

        response = client.post(USER_INVITATION_URL.format(invitations[0].id),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Invitation')
