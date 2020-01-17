from unittest.mock import Mock, patch
from .mocks import fake
from api.utils.token_validator import TokenValidator
from .assertions import (assert_send_grid_mock_send,
                         assert_successful_response,
                         assert_when_token_is_missing,
                         assert_when_token_is_invalid,
                         assert_reg_confirm_email_was_sent_properly)
from api.utils.success_messages import (CREATED, LOGIN, CONFIRM_EMAIL_RESENT,
                                        REG_VERIFIED, RESET_PASS_MAIL,
                                        PASSWORD_CHANGED)
from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.constants import CONFIRM_TOKEN, RESET_TOKEN
from api.models import User
from .mocks.user import UserGenerator
from .mocks.redis import RedisMock
from dateutil import parser
from datetime import datetime, timezone
import json

REGISTER_URL = '/api/auth/register'
LOGIN_URL = '/api/auth/login'
RESEND_EMAIL_ENDPOINT = 'api/auth/resend-email'
CONFIRM_EMAIL_ENDPOINT = 'api/auth/confirm/{}'
RESET_PASSWORD_ENDPOINT = 'api/auth/reset'
CONFIRM_RESET_PASSWORD_ENDPOINT = 'api/auth/reset/confirm'


class TestLogoutEndpoint:
    def test_should_logout_user_successfully(self, init_db, client):
        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']

        user = UserGenerator.generate_model_obj(save=True)
        user.redirect_url = redirect_url
        user.update()
        token = UserGenerator.generate_token(user, token_type=CONFIRM_TOKEN)
        client.set_cookie('/', 'token', token)
        response = client.delete(LOGIN_URL)

        cookie = response.headers.get('Set-Cookie')
        cookie_args = cookie.split(';')
        exp_value = None
        for arg in cookie_args:
            if 'Expires' in arg or 'expires' in arg:
                exp_value = parser.parse(arg.split('=')[1])
                break
        assert response.status_code == 200
        assert exp_value < datetime.now(tz=timezone.utc)
        assert 'token=deleted' in cookie


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
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error['login_failed']

    def test_should_fail_when_field_are_not_provided(self, init_db, client):

        response = client.post(LOGIN_URL,
                               data=json.dumps({}),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['usernameOrEmail'][
            0] == serialization_error['required']
        assert response_body['errors']['password'][0] == serialization_error[
            'required']


class TestLinkClickedFromUserEmail:
    def test_user_should_be_verified_successfully_when_token_is_valid(
            self, init_db, client):
        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']
        confirm_id = 'some-id'
        user = UserGenerator.generate_model_obj(save=True)
        user.redirect_url = redirect_url
        user.update()
        token = UserGenerator.generate_token(user, token_type=CONFIRM_TOKEN)
        RedisMock.set(confirm_id, token)

        assert RedisMock.get(confirm_id) == token
        response = client.get(CONFIRM_EMAIL_ENDPOINT.format(confirm_id),
                              content_type="application/json")
        assert RedisMock.get(
            confirm_id
        ) is None  # check that it was removed from redis ie delete is called
        assert response.status_code == 302
        assert response.headers.get('Location') == \
            f"{redirect_url}?success=true&message={REG_VERIFIED.replace(' ', '%20')}"

    def test_should_respond_with_appropriate_message_when_token_is_expired(
            self, init_db, client):
        redirect_url = UserGenerator.generate_api_input_data()['redirectURL']
        confirm_id = 'some-id'
        user = UserGenerator.generate_model_obj(save=True)
        user.redirect_url = redirect_url
        token = UserGenerator.generate_token(user,
                                             token_type=CONFIRM_TOKEN,
                                             seconds=-1)
        RedisMock.set(confirm_id, token)
        assert RedisMock.get(confirm_id) == token

        response = client.get(CONFIRM_EMAIL_ENDPOINT.format(confirm_id),
                              content_type="application/json")

        message = authentication_errors['confirmation_expired'].replace(
            ' ', '%20')

        assert RedisMock.get(
            confirm_id
        ) is None  # check that it was removed from redis ie delete is called
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
        RedisMock.flush_all()
        response = client.get(CONFIRM_EMAIL_ENDPOINT.format('some-invalid-ID'),
                              content_type="application/json")

        assert RedisMock.get('some-invalid-ID') is None  # was not
        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'invalid_confirmation_link']


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestResendEmail:
    def test_user_should_be_able_to_resend_email_when_he_has_not_verified_account(
            self, mock_send, init_db, client):
        from api.utils.emails import EmailUtil
        RedisMock.flush_all()
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
        html_content = assert_send_grid_mock_send(mock_send, user.email)

        set_key = list(RedisMock.cache.keys())[0]  # the only key in token_key
        exp_key = list(
            RedisMock.expired_cache.keys())[0]  # the only key in expired_key

        token = RedisMock.get(set_key)
        token_duration = RedisMock.expired_cache[exp_key]

        token_data = TokenValidator.decode_token_data(token, CONFIRM_TOKEN)
        assert token_data['id'] == user.id

        assert exp_key == set_key  # checks that the key was expired to a time in the future
        assert token_duration == 60 * 14.5  # tests the amount of time token should last
        assert_reg_confirm_email_was_sent_properly(html_content, redirect_url,
                                                   user, token, set_key)

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
        assert mock_send.called is False

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
        # assert mock_send.called == mock_redis_expire.called == mock_redis_set.called
        assert mock_send.called is False

    def test_it_should_fail_when_token_is_not_provided(self, mock_send,
                                                       init_db, client):
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               content_type="application/json")
        assert_when_token_is_missing(response)
        assert mock_send.called is False

    def test_it_should_fail_when_token_is_invalid(self, mock_send, init_db,
                                                  client):
        client.set_cookie('/', 'token', 'some-invalid-token')
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               content_type="application/json")
        assert_when_token_is_invalid(response)
        assert mock_send.called is False


class TestConfirmResetPassword:
    def test_user_should_be_able_to_reset_their_password_once_reset_token_is_provided(
            self, init_db, client):
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user, token_type=RESET_TOKEN)
        RedisMock.flush_all()
        new_password = 'some-very-new-password'
        mock_reset_id = 'mock_id'
        RedisMock.set(mock_reset_id, token)
        valid_data = json.dumps({
            'password': new_password,
            'resetId': mock_reset_id
        })

        assert RedisMock.get(mock_reset_id) == token
        response = client.patch(CONFIRM_RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json")
        response_body = json.loads(response.data)
        user = User.query.get(user.id)
        assert RedisMock.get(
            mock_reset_id) is None  # this means that delete was called
        assert len(RedisMock.expired_cache) == 0  # expired was not called
        assert user.verify_password(new_password)
        assert response.status_code == 200
        assert response_body['message'] == PASSWORD_CHANGED

    def test_error_message_should_be_sent_when_password_is_not_provided(
            self, init_db, client):
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user, token_type=RESET_TOKEN)
        valid_data = json.dumps({})
        response = client.patch(CONFIRM_RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json",
                                headers={'Authorization': f'Bearer {token}'})
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['resetId'][0] == serialization_error[
            'required']
        assert response_body['errors']['password'][0] == serialization_error[
            'required']

    def test_should_fail_with_appropriate_message_when_reset_id_is_invalid(
            self, init_db, client):
        RedisMock.flush_all()
        new_password = 'some-very-new-password'
        reset_id = 'resetID'
        valid_data = json.dumps({
            'password': new_password,
            'resetId': reset_id,
        })
        response = client.patch(CONFIRM_RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == authentication_errors[
            'invalid_reset_link']

        assert RedisMock.get(reset_id) is None

    def test_should_fail_with_appropriate_message_when_token_is_expired(
            self, init_db, client):
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user,
                                             token_type=RESET_TOKEN,
                                             seconds=-40)
        new_password = 'some-very-new-password'
        reset_id = 'resetID'
        RedisMock.set(reset_id, token)
        valid_data = json.dumps({
            'password': new_password,
            'resetId': reset_id,
        })
        assert RedisMock.get(reset_id) == token
        response = client.patch(CONFIRM_RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == authentication_errors[
            'invalid_reset_link']

        assert RedisMock.get(reset_id) is None  # delete was called
        assert len(RedisMock.expired_cache) == 0  #  expired  was not called


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestResetPassword:
    def test_user_should_be_able_to_make_reset_request_when_account_exists(
            self, mock_send, init_db, client):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        user = UserGenerator.generate_model_obj(save=True)
        redirect_url = fake.url()
        valid_data = json.dumps({
            'email': user.email,
            'redirectURL': redirect_url,
        })
        RedisMock.flush_all()
        response = client.patch(RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json")

        assert EmailUtil.send_mail_as_html.delay.called
        assert len(RedisMock.expired_cache) == len(
            RedisMock.cache) == 1  # expired and set were called once
        html_to_check_for = '<h1>Reset Account</h1>'
        assert_successful_response(response,
                                   RESET_PASS_MAIL.format(user.email))
        html_content = assert_send_grid_mock_send(mock_send, user.email)

        set_key = list(RedisMock.cache.keys())[0]
        reset_id = list(RedisMock.expired_cache.keys())[0]
        exp_duration = RedisMock.expired_cache[reset_id]
        token = RedisMock.get(set_key)
        # Extracting token from HTML content
        decoded = TokenValidator.decode_token(token, RESET_TOKEN)
        decoded_data = decoded['data']

        assert set_key == reset_id
        # Validating token
        assert html_to_check_for in html_content
        assert f'{redirect_url}/{reset_id}' in html_content
        assert decoded_data['email'] == user.email
        assert decoded_data['type'] == RESET_TOKEN
        assert decoded_data['id'] == user.id

        assert exp_duration == 14.5 * 60
        # checks that the expiry time is 15 minutes
        assert decoded['exp'] - decoded['iat'] == 15 * 60

    def test_should_return_appropriate_error_when_email_is_not_found(
            self, mock_send, init_db, client):
        RedisMock.flush_all()
        invalid_data = json.dumps({
            'email': 'some-random-email@email.com',
            'redirectURL': fake.url(),
        })
        response = client.patch(RESET_PASSWORD_ENDPOINT,
                                data=invalid_data,
                                content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'email_not_found']
        assert response_body['status'] == 'error'
        assert not mock_send.called
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 0

    def test_should_fail_when_redirect_url_is_not_provided(
            self, mock_send, init_db, client):
        RedisMock.flush_all()
        user = UserGenerator.generate_model_obj(save=True)
        invalid_data = json.dumps({
            'email': user.email,
        })
        response = client.patch(RESET_PASSWORD_ENDPOINT,
                                data=invalid_data,
                                content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert 'redirectURL' in response_body['errors']
        assert response_body['status'] == 'error'
        assert not mock_send.called
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 0


@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestRegisterEndpoint:
    def test_new_user_should_register_successfully_when_valid_data_is_provided_and_should_be_added_to_the_db(
            self, mock_send, init_db, client):
        from api.utils.emails import EmailUtil
        RedisMock.flush_all()
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        valid_user_dict = UserGenerator.generate_api_input_data()
        response = client.post(REGISTER_URL,
                               data=json.dumps(valid_user_dict),
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
        html_content = assert_send_grid_mock_send(mock_send, user.email)

        # Check redis interactions
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1

        key = list(RedisMock.cache.keys())[0]
        token = RedisMock.cache.get(key)
        exp_key = list(RedisMock.expired_cache.keys())[0]
        exp_time = RedisMock.expired_cache.get(exp_key)

        assert key == exp_key
        assert exp_time == 14.5 * 60
        assert token
        assert_reg_confirm_email_was_sent_properly(
            html_content, valid_user_dict['redirectURL'], user, token, key)

    def test_attempt_to_register_user_with_invalid_data_should_fail(
            self, mock_send, init_db, client):
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

        assert mock_send.called is False
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1

    def test_attempt_to_register_user_with_first_name_or_last_name_gt_20_should_fail(
            self, mock_send, init_db, client):
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

        assert mock_send.called is False
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1

    def test_attempt_to_register_user_with_first_name_or_last_name_lt_3_chars_should_fail(
            self, mock_send, init_db, client):
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

        assert mock_send.called is False
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1

    def test_attempt_to_register_a_user_with_existing_email_should_fail(
            self, mock_send, init_db, client):
        valid_user_obj = UserGenerator.generate_model_obj(save=True)
        user_data = {
            'username': 'someotherusername',
            'firstName': valid_user_obj.first_name,
            'lastName': valid_user_obj.last_name,
            'email': valid_user_obj.email,
            'password': 'some-unnknown-password',
            'redirectURL': 'http://some-url.com',
        }

        response = client.post(REGISTER_URL,
                               data=json.dumps(user_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 409
        assert 'data' not in response_body
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'already_exists'].format('`email` or `username`')
        assert mock_send.called is False
        assert len(RedisMock.expired_cache) == len(RedisMock.cache) == 1
