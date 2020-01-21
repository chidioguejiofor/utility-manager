from unittest.mock import patch, Mock
from api.utils.success_messages import ADDED_TO_ORG
from api.utils.error_messages import authentication_errors, serialization_error
from api.models import Membership
from api.utils.constants import APP_EMAIL
from tests.mocks.user import UserGenerator

from tests.assertions import assert_send_grid_mock_send

import json
import math

RESEND_INVITATION_URL = '/api/org/{}/invitations/{}/resend'

INVITE_KEY = 'invites'


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestAdminResendInvitation:
    def test_admin_should_be_able_to_resend_invitations(
            self, mock_email_send, init_db, client,
            saved_organisation_invitations):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        user_objs, org, user_ids, invitations, regular_user_id = \
            saved_organisation_invitations(1)

        token = UserGenerator.generate_token(org.creator)
        client.set_cookie('/', 'token', token)
        request_data = {
            "userDashboardURL": "http://localhost:8080/dashboard",
            "signupURL": "http://localhost:8080",
        }
        url = RESEND_INVITATION_URL.format(org.id, invitations[0].id)
        response = client.post(url,
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        print(response_body)
        assert response.status_code == 202
        assert response_body['status'] == 'success'
        assert response_body['message'] == 'Invitation was re-sent.'

        assert EmailUtil.send_mail_as_html.delay.called

        subject, receivers, html = EmailUtil.send_mail_as_html.delay.call_args[
            0]
        blind_copies = EmailUtil.send_mail_as_html.delay.call_args[1][
            'blind_copies']

        assert_send_grid_mock_send(mock_email_send,
                                   receivers,
                                   num_of_calls=1,
                                   bccs=blind_copies)
        assert_send_grid_mock_send(mock_email_send, [APP_EMAIL],
                                   num_of_calls=1,
                                   bccs=[invitations[0].email])

    def test_should_return_a_404_when_organisation_is_not_found(
            self, mock_email_send, app, init_db,
            saved_organisation_invitations, client):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        user_objs, org, user_ids, invitations, regular_user_id = \
            saved_organisation_invitations(1)

        token = UserGenerator.generate_token(org.creator)
        client.set_cookie('/', 'token', token)
        request_data = {
            "userDashboardURL": "http://localhost:8080/dashboard",
            "signupURL": "http://localhost:8080",
        }
        url = RESEND_INVITATION_URL.format('invalid_org_id', invitations[0].id)
        response = client.post(url,
                               data=json.dumps(request_data),
                               content_type="application/json")

        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['status'] == 'error'

        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation id')

        # Check the the email calls were handled properly
        assert not EmailUtil.send_mail_as_html.delay.called
        assert not mock_email_send.called

    def test_should_return_a_404_when_invitation_id_is_not_found(
            self, mock_email_send, app, init_db,
            saved_organisation_invitations, client):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        user_objs, org, user_ids, invitations, regular_user_id = \
            saved_organisation_invitations(1)

        token = UserGenerator.generate_token(org.creator)
        client.set_cookie('/', 'token', token)
        request_data = {
            "userDashboardURL": "http://localhost:8080/dashboard",
            "signupURL": "http://localhost:8080",
        }
        url = RESEND_INVITATION_URL.format(org.id, 'invalid_invitaion_id')
        response = client.post(url,
                               data=json.dumps(request_data),
                               content_type="application/json")

        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['status'] == 'error'

        assert response_body['message'] == serialization_error[
            'not_found'].format('Invitation')

        # Check the the email calls were handled properly
        assert not EmailUtil.send_mail_as_html.delay.called
        assert not mock_email_send.called