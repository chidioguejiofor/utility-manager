from unittest.mock import patch, Mock
from api.models import Membership, Role, Invitation, db, User, Organisation
from api.utils.constants import APP_EMAIL
from api.utils.error_messages import serialization_error, invitation_errors, authentication_errors
from api.utils.success_messages import INVITING_USER_MSG_DICT
from tests.mocks.user import UserGenerator
from tests.mocks.redis import RedisMock
from tests.mocks.organisation import OrganisationGenerator
from tests.assertions import assert_send_grid_mock_send, add_cookie_to_client
import json

INVITATION_URL = '/api/org/{}/invitations'
INVITE_KEY = 'invites'


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestInviteUserToOrganisation:
    @staticmethod
    def create_test_precondition(role_list, num_of_emails=3):
        Membership.query.delete()
        Organisation.query.delete()
        User.query.delete()
        Invitation.query.delete()
        db.session.commit()
        org = OrganisationGenerator.generate_model_obj(save=True,
                                                       verify_user=True)
        emails = []
        invitation_request = []
        for i in range(0, num_of_emails):
            email = f'email{i+1}@email.com'
            emails.append(email)
            invitation_request.append({
                'email': email,
                'roleId': role_list[i % len(role_list)]
            })

        request_data = {
            "userDashboardURL": "http://localhost:8080/dashboard",
            "signupURL": "http://localhost:8080",
            INVITE_KEY: invitation_request,
        }
        return org, emails, invitation_request, request_data

    def test_all_invitations_should_be_created_when_there_have_not_been_sent_previously(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)
        emails = set(emails)

        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 201
        assert response_body['status'] == 'success'
        assert len(response_body['data']['success']) == 3
        assert len(response_body['data']['failed']) == 0
        assert response_body['message'] == INVITING_USER_MSG_DICT['success']

        for res in response_body['data']['success']:
            assert res['email'] in emails
            assert res['userDashboardURL'] == request_data['userDashboardURL']
            assert res['signupURL'] == request_data['signupURL']

        # Check the the email calls were sent properly
        assert mock_send_html_delay.called

        subject, receivers, html = mock_send_html_delay.call_args[0]
        blind_copies = mock_send_html_delay.call_args[1]['blind_copies']
        assert mock_email_send.called
        assert_send_grid_mock_send(mock_email_send,
                                   receivers,
                                   num_of_calls=1,
                                   bccs=blind_copies)
        assert_send_grid_mock_send(mock_email_send, [APP_EMAIL],
                                   num_of_calls=1,
                                   bccs=emails)

    def test_redis_roles_should_be_properly_cached_the_role_of_the_user_making_the_request(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)

        token = UserGenerator.generate_token(
            org.creator)  # By default the creator becomes the owner
        add_cookie_to_client(client, org.creator, token)
        client.post(INVITATION_URL.format(org.id),
                    data=json.dumps(request_data),
                    content_type="application/json")

        # Tests for redis
        owner_role_id = Role.query.filter_by(name='OWNER').first().id
        assert RedisMock.get('ROLE_OWNER') == owner_role_id

    def test_should_fail_when_an_admin_tries_to_add_an_owner_role(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        owner_role_id = Role.query.filter_by(name='OWNER').first().id
        admin_role_id = Role.query.filter_by(name='ADMIN').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [owner_role_id, manager_role_id], 3)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        Membership(organisation_id=org.id,
                   user_id=user.id,
                   role_id=admin_role_id).save()

        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert response_body['errors'][INVITE_KEY]['0']['roleId'][
            0] == invitation_errors['cannot_add_role'].format('OWNER')
        assert response_body['errors'][INVITE_KEY]['2']['roleId'][
            0] == invitation_errors['cannot_add_role'].format('OWNER')
        assert response_body['message'] == serialization_error[
            'invalid_field_data']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_fail_when_the_user_is_not_an_admin_or_owner(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        Membership(organisation_id=org.id,
                   user_id=user.id,
                   role_id=regular_user_role_id).save()

        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 403
        assert response_body['status'] == 'error'

        assert response_body['message'] == authentication_errors[
            'forbidden'].format('add roles')

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_return_a_404_when_organisation_is_not_found(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        admin_role_id = Role.query.filter_by(name='ADMIN').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        Membership(organisation_id=org.id,
                   user_id=user.id,
                   role_id=admin_role_id).save()

        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        response = client.post(
            INVITATION_URL.format('invalid_id'),  # invalid org_id
            data=json.dumps(request_data),
            content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['status'] == 'error'

        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_fail_when_the_owner_tries_to_add_an_owner_role(  # You can't have 2 owners
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        owner_role_id = Role.query.filter_by(name='OWNER').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [owner_role_id, manager_role_id], 3)

        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert response_body['errors'][INVITE_KEY]['0']['roleId'][
            0] == invitation_errors['cannot_add_role'].format('OWNER')
        assert response_body['errors'][INVITE_KEY]['2']['roleId'][
            0] == invitation_errors['cannot_add_role'].format('OWNER')
        assert response_body['message'] == serialization_error[
            'invalid_field_data']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_fail_when_an_admin_tries_to_add_an_admin(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        admin_role_id = Role.query.filter_by(name='ADMIN').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [admin_role_id, manager_role_id], 3)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        Membership(
            user_id=user.id,
            organisation_id=org.id,
            role_id=admin_role_id,
        ).save()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert response_body['errors'][INVITE_KEY]['0']['roleId'][
            0] == invitation_errors['cannot_add_role'].format('ADMIN')
        assert response_body['errors'][INVITE_KEY]['2']['roleId'][
            0] == invitation_errors['cannot_add_role'].format('ADMIN')
        assert response_body['message'] == serialization_error[
            'invalid_field_data']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_when_all_the_invites_already_exists_they_should_all_fail(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):

        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)
        invitation_models = [
            Invitation(organisation_id=org.id,
                       email=inv['email'],
                       role_id=inv['roleId'],
                       user_dashboard_url=request_data['userDashboardURL'],
                       signup_url=request_data['signupURL'])
            for inv in invitation_request
        ]

        Invitation.bulk_create(invitation_models)
        emails = set(emails)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert len(response_body['data']['success']) == 0
        assert len(response_body['data']['failed']) == len(invitation_request)
        assert response_body['message'] == INVITING_USER_MSG_DICT['error']

        for res in response_body['data']['failed']:
            assert res['email'] in emails
            assert res['message'] == invitation_errors[
                'invites_already_sent_to_email']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_all_invitations_should_fail_when_at_least_one_invite_is_contains_an_invalid_role_id(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):

        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            ['some-invalid_id', manager_role_id, regular_user_role_id], 3)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)

        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['status'] == 'error'

        assert response_body['message'] == invitation_errors[
            'missing_role_ids']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_have_a_partial_success_when_some_emails_exists_and_some_dont(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)
        token = UserGenerator.generate_token(org.creator)
        invitation_models = [
            Invitation(organisation_id=org.id,
                       email=inv['email'],
                       role_id=inv['roleId'],
                       user_dashboard_url=request_data['userDashboardURL'],
                       signup_url=request_data['signupURL'])
            for inv in invitation_request[1:]  # from index 1 to the end
        ]
        success_email = {*emails[:1]}
        failure_emails = {*emails[1:]}
        Invitation.bulk_create(invitation_models)

        add_cookie_to_client(client, org.creator, token)

        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 207
        assert response_body['status'] == 'partial'
        assert len(response_body['data']['success']) == 1
        assert len(response_body['data']['failed']) == 2
        assert response_body['message'] == INVITING_USER_MSG_DICT['partial']

        for res in response_body['data']['failed']:
            assert res['email'] in failure_emails
            assert res['message'] == invitation_errors[
                'invites_already_sent_to_email']

        for res in response_body['data']['success']:
            assert res['email'] in success_email
            assert res['userDashboardURL'] == request_data['userDashboardURL']
            assert res['signupURL'] == request_data['signupURL']

        # Check the the email calls were sent properly
        assert mock_send_html_delay.called

        subject, receivers, html = mock_send_html_delay.call_args[0]
        blind_copies = mock_send_html_delay.call_args[1]['blind_copies']
        assert mock_email_send.called
        assert_send_grid_mock_send(mock_email_send,
                                   receivers,
                                   num_of_calls=1,
                                   bccs=blind_copies)
        assert_send_grid_mock_send(mock_email_send, [APP_EMAIL],
                                   num_of_calls=1,
                                   bccs=success_email)

    def test_should_have_a_partial_success_when_some_emails_are_already_in_organisation(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)
        token = UserGenerator.generate_token(org.creator)

        user_models = [
            UserGenerator.generate_model_obj(email=inv['email'],
                                             save=False,
                                             verified=True)
            for inv in invitation_request[1:]
        ]

        user_models = User.bulk_create(user_models, commit=True)

        memberships = [
            Membership(user_id=user.id,
                       role_id=regular_user_role_id,
                       organisation_id=org.id) for user in user_models
        ]
        Membership.bulk_create(memberships, commit=True)

        success_email = {*emails[:1]}
        failure_emails = {*emails[1:]}

        add_cookie_to_client(client, org.creator, token)

        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 207
        assert response_body['status'] == 'partial'
        assert len(response_body['data']['success']) == 1
        assert len(response_body['data']['failed']) == 2
        assert response_body['message'] == INVITING_USER_MSG_DICT['partial']

        for res in response_body['data']['failed']:
            assert res['email'] in failure_emails
            assert res['message'] == invitation_errors['email_already_in_org']

        for res in response_body['data']['success']:
            assert res['email'] in success_email
            assert res['userDashboardURL'] == request_data['userDashboardURL']
            assert res['signupURL'] == request_data['signupURL']

        # Check the the email calls were sent properly
        assert mock_send_html_delay.called

        subject, receivers, html = mock_send_html_delay.call_args[0]
        blind_copies = mock_send_html_delay.call_args[1]['blind_copies']
        assert mock_email_send.called
        assert_send_grid_mock_send(mock_email_send,
                                   receivers,
                                   num_of_calls=1,
                                   bccs=blind_copies)
        assert_send_grid_mock_send(mock_email_send, [APP_EMAIL],
                                   num_of_calls=1,
                                   bccs=success_email)

    def test_when_all_the_invites_are_already_in_org_all_should_fail(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):

        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 3)

        user_models = [
            UserGenerator.generate_model_obj(email=inv['email'],
                                             save=False,
                                             verified=True)
            for inv in invitation_request
        ]

        user_models = User.bulk_create(user_models, commit=True)

        memberships = [
            Membership(user_id=user.id,
                       role_id=regular_user_role_id,
                       organisation_id=org.id) for user in user_models
        ]
        Membership.bulk_create(memberships, commit=True)
        emails = set(emails)
        token = UserGenerator.generate_token(org.creator)

        add_cookie_to_client(client, org.creator, token)

        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert len(response_body['data']['success']) == 0
        assert len(response_body['data']['failed']) == 3
        assert response_body['message'] == INVITING_USER_MSG_DICT['error']

        for res in response_body['data']['failed']:
            assert res['email'] in emails
            assert res['message'] == invitation_errors['email_already_in_org']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_fail_when_duplicate_email_is_specified_in_request(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 4)
        request_data[INVITE_KEY][1]['email'] = request_data[INVITE_KEY][0][
            'email']
        request_data[INVITE_KEY][3]['email'] = request_data[INVITE_KEY][2][
            'email']

        token = UserGenerator.generate_token(org.creator)

        add_cookie_to_client(client, org.creator, token)

        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert response_body['errors'][INVITE_KEY]['1']['email'][
            0] == invitation_errors['duplicate_email_in_request']
        assert response_body['errors'][INVITE_KEY]['3']['email'][
            0] == invitation_errors['duplicate_email_in_request']
        assert response_body['message'] == serialization_error[
            'invalid_field_data']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    #
    def test_should_fail_when_the_email_or_role_id_key_is_missing_in_any_item_on_the_list(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        regular_user_role_id = Role.query.filter_by(
            name='REGULAR USERS').first().id
        manager_role_id = Role.query.filter_by(name='MANAGER').first().id
        org, emails, invitation_request, request_data = self.create_test_precondition(
            [regular_user_role_id, manager_role_id], 4)
        request_data[INVITE_KEY][1] = {
            'roleId': request_data[INVITE_KEY][1]['roleId']
        }
        request_data[INVITE_KEY][2] = {
            'email': request_data[INVITE_KEY][2]['email']
        }
        request_data[INVITE_KEY][3] = {}
        token = UserGenerator.generate_token(org.creator)

        add_cookie_to_client(client, org.creator, token)
        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert response_body['errors'][INVITE_KEY]['1']['email'][
            0] == serialization_error['required']
        assert response_body['errors'][INVITE_KEY]['2']['roleId'][
            0] == serialization_error['required']
        assert response_body['errors'][INVITE_KEY]['3']['email'][
            0] == serialization_error['required']
        assert response_body['errors'][INVITE_KEY]['3']['roleId'][
            0] == serialization_error['required']

        assert response_body['message'] == serialization_error[
            'invalid_field_data']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called

    def test_should_fail_when_the_required_keys_are_missing(
            self, mock_email_send, mock_send_html_delay, app, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True,
                                                       verify_user=True)
        request_data = {}

        token = UserGenerator.generate_token(org.creator)

        add_cookie_to_client(client, org.creator, token)

        response = client.post(INVITATION_URL.format(org.id),
                               data=json.dumps(request_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['status'] == 'error'
        assert response_body['errors'][INVITE_KEY][0] == serialization_error[
            'required']
        assert response_body['errors']['signupURL'][0] == serialization_error[
            'required']
        assert response_body['errors']['userDashboardURL'][
            0] == serialization_error['required']
        assert response_body['message'] == serialization_error[
            'invalid_field_data']

        # Check the the email calls were handled properly
        assert not mock_send_html_delay.called
        assert not mock_email_send.called
