from unittest.mock import Mock, patch
from .assertions import (assert_send_grid_mock_send,
                         assert_successful_response,
                         assert_when_token_is_missing,
                         assert_when_token_is_invalid)
from api.utils.success_messages import CREATED, LOGIN, CONFIRM_EMAIL_RESENT, REG_VERIFIED
from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.constants import CONFIRM_TOKEN
from api.models import User
from .mocks.user import UserGenerator
import time
import json

REGISTER_URL = '/api/auth/register'
LOGIN_URL = '/api/auth/login'
RESEND_EMAIL_ENDPOINT = 'api/auth/resend-email'
CONFIRM_EMAIL_ENDPOINT = 'api/auth/confirm/{}'


class TestLoginEndpoint:
    def test_user_should_be_logged_in_once_correct_email_and_password_is_provided(
            self, init_db, client):
        valid_user = UserGenerator.generate_model_obj(save=True)
        user_data = {
            'usernameOrEmail': valid_user.email,
            'password': valid_user.password,
        }
        response = client.post(LOGIN_URL,
                               data=json.dumps(user_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        response_data = response_body['data']
        user = User.query.filter(User.email == response_data['email']).first()
        assert response.status_code == 200
        assert 'data' in response_body
        assert user.first_name == response_data['firstName']
        assert user.last_name == response_data['lastName']
        assert response_body['status'] == 'success'
        assert response_body['message'] == LOGIN

    def test_user_should_be_logged_in_once_correct_username_and_password_is_provided(
            self, init_db, client):
        valid_user = UserGenerator.generate_model_obj(save=True)
        user_data = {
            'usernameOrEmail': valid_user.username,
            'password': valid_user.password,
        }
        response = client.post(LOGIN_URL,
                               data=json.dumps(user_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        response_data = response_body['data']
        user = User.query.filter(User.email == response_data['email']).first()
        assert response.status_code == 200
        assert 'data' in response_body
        assert user.first_name == response_data['firstName']
        assert user.last_name == response_data['lastName']
        assert response_body['status'] == 'success'
        assert response_body['message'] == LOGIN

    def test_login_should_fail_when_user_password_is_incorrect(
            self, init_db, client):
        valid_user = UserGenerator.generate_model_obj(save=True)
        user_data = {
            'usernameOrEmail': valid_user.username,
            'password': 'some_very_invalid2384798_thing.password',
        }
        response = client.post(LOGIN_URL,
                               data=json.dumps(user_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        print(response_body)
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error['login_failed']


class TestLinkClickedFromUserEmail:
    def test_user_should_be_verified_successfully_when_token_is_valid(
            self, init_db, client):

        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']

        user = UserGenerator.generate_model_obj(save=True)
        user.redirect_url = redirect_url
        user.update()
        token = UserGenerator.generate_token(user, token_type=CONFIRM_TOKEN)
        client.set_cookie('/', 'token', token)
        response = client.get(CONFIRM_EMAIL_ENDPOINT.format(token),
                              content_type="application/json")

        assert response.status_code == 302
        assert response.headers.get('Location') == \
            f"{redirect_url}?success=true&message={REG_VERIFIED.replace(' ', '%20')}"

    def test_should_respond_with_appropriate_message_when_token_is_expired(
            self, init_db, client):
        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']
        user = UserGenerator.generate_model_obj(save=True)
        user.redirect_url = redirect_url
        token = UserGenerator.generate_token(user,
                                             token_type=CONFIRM_TOKEN,
                                             seconds=-1)
        time.sleep(0.1)
        response = client.get(CONFIRM_EMAIL_ENDPOINT.format(token),
                              content_type="application/json")

        message = authentication_errors['confirmation_expired'].replace(
            ' ', '%20')
        assert response.status_code == 302
        assert response.headers.get('Location') == \
               f"{redirect_url}?success=false&message={message}"

    def test_should_return_json_when_the_link_is_invalid(
            self, init_db, client):
        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']
        user = UserGenerator.generate_model_obj(save=True)
        user.redirect_url = redirect_url
        token = UserGenerator.generate_token(user,
                                             token_type=CONFIRM_TOKEN,
                                             seconds=-1)
        time.sleep(0.1)
        response = client.get(
            CONFIRM_EMAIL_ENDPOINT.format('some-invalid-token'),
            content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'invalid_confirmation_link']


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestResendEmail:
    def test_user_should_be_able_to_resend_email_when_he_has_not_verified_account(
            self, mock_send, init_db, client):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']
        valid_data = json.dumps({'redirectURL': redirect_url})
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               data=valid_data,
                               content_type="application/json")

        assert_successful_response(response,
                                   CONFIRM_EMAIL_RESENT.format(user.email))
        assert_send_grid_mock_send(mock_send, user.email)

    def test_when_redirect_email_is_invalid_should_fail(
            self, mock_send, init_db, client):
        valid_data = json.dumps({'redirectURL': 'ftp://here.com'})
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               data=valid_data,
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == serialization_error[
            'invalid_url'].format('Redirect URL')
        assert response_body['status'] == 'error'

    def test_it_should_error_when_the_user_is_already_verified(
            self, mock_send, init_db, client):

        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']
        valid_data = json.dumps({'redirectURL': redirect_url})
        user = UserGenerator.generate_model_obj()
        user.verified = True
        user.save()
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               data=valid_data,
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == serialization_error[
            'already_verified']
        assert response_body['status'] == 'error'

    def test_it_should_fail_when_token_is_not_provided(self, mock_send,
                                                       init_db, client):
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               content_type="application/json")
        assert_when_token_is_missing(response)

    def test_it_should_fail_when_token_is_invalid(self, mock_send, init_db,
                                                  client):
        client.set_cookie('/', 'token', 'some-invalid-token')
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               content_type="application/json")
        assert_when_token_is_invalid(response)


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestRegisterEndpoint:
    def test_new_user_should_register_successfully_when_valid_data_is_provided_and_should_be_added_to_the_db(
            self, mock_send, init_db, client):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        valid_user_json = UserGenerator.generate_api_input_json_data()
        response = client.post(REGISTER_URL,
                               data=valid_user_json,
                               content_type="application/json")
        response_body = json.loads(response.data)
        response_data = response_body['data']
        user = User.query.filter(User.email == response_data['email']).first()
        assert response.status_code == 201
        assert 'data' in response_body
        assert user.first_name == response_data['firstName']
        assert user.last_name == response_data['lastName']
        assert response_body['status'] == 'success'
        assert response_body['message'] == CREATED.format('user')
        assert_send_grid_mock_send(mock_send, user.email)

    def test_attempt_to_register_user_with_invalid_data_should_fail(
            self, init_db, client):
        invalid_user_json = UserGenerator.generate_api_input_data()
        invalid_user_json.update(email='Invalid stuff',
                                 firstName='^*&*&&*^',
                                 username='^user?')
        response = client.post(REGISTER_URL,
                               data=json.dumps(invalid_user_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert 'username' in response_body['errors']
        assert 'firstName' in response_body['errors']
        assert 'email' in response_body['errors']

    def test_attempt_to_register_user_with_first_name_or_last_name_gt_20_should_fail(
            self, init_db, client):
        invalid_user_json = UserGenerator.generate_api_input_data()
        invalid_user_json.update(
            firstName='ThisFirstNameIsGreaterThan20CharactersWhatAName',
            lastName='ThisLastNameIsGreaterThan20CharactersWhatAName',
        )
        response = client.post(REGISTER_URL,
                               data=json.dumps(invalid_user_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert 'firstName' in response_body['errors']
        assert response_body['errors']['firstName'][0] == serialization_error[
            'max_length_error'].format(20)
        assert response_body['errors']['lastName'][0] == serialization_error[
            'max_length_error'].format(20)

    def test_attempt_to_register_user_with_first_name_or_last_name_lt_3_chars_should_fail(
            self, init_db, client):
        invalid_user_json = UserGenerator.generate_api_input_data()
        invalid_user_json.update(
            firstName='a',
            lastName='b',
        )
        response = client.post(REGISTER_URL,
                               data=json.dumps(invalid_user_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert 'firstName' in response_body['errors']
        assert response_body['errors']['firstName'][0] == serialization_error[
            'min_length_error'].format(3)
        assert response_body['errors']['firstName'][0] == serialization_error[
            'min_length_error'].format(3)

    def test_attempt_to_register_a_user_with_existing_email_should_fail(
            self, init_db, client):
        valid_user_json = UserGenerator.generate_api_input_json_data()
        client.post(REGISTER_URL,
                    data=valid_user_json,
                    content_type="application/json")
        user_data = json.loads(valid_user_json)
        user_data['email'] = 'temp@email.com'

        response = client.post(REGISTER_URL,
                               data=json.dumps(user_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 409
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'already_exists'].format('email or username')
