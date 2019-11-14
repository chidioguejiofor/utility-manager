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
import time
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
        assert response.status_code == 200
        assert 'expires=Thu, 01 Jan 1970 00:00:00 GMT' in cookie
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


@patch('api.services.redis_util.RedisUtil.REDIS.set', autospec=True)
@patch('api.services.redis_util.RedisUtil.REDIS.expire', autospec=True)
@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestResendEmail:
    def test_user_should_be_able_to_resend_email_when_he_has_not_verified_account(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        html_content = assert_send_grid_mock_send(mock_send, user.email)
        set_key, token = mock_redis_set.call_args[0]
        exp_key, token_duration = mock_redis_expire.call_args[0]
        token_data = TokenValidator.decode_token_data(token, CONFIRM_TOKEN)
        assert token_data['id'] == user.id
        assert exp_key == set_key
        assert token_duration == 60 * 14.5
        assert_reg_confirm_email_was_sent_properly(html_content, redirect_url,
                                                   user, token, set_key)

    def test_when_redirect_email_is_invalid_should_fail(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        assert mock_send.called == mock_redis_expire.called == mock_redis_set.called
        assert mock_send.called is False

    def test_it_should_error_when_the_user_is_already_verified(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):

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
        assert mock_send.called == mock_redis_expire.called == mock_redis_set.called
        assert mock_send.called is False

    def test_it_should_fail_when_token_is_not_provided(self, mock_send,
                                                       mock_redis_expire,
                                                       mock_redis_set, init_db,
                                                       client):
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               content_type="application/json")
        assert_when_token_is_missing(response)
        assert mock_send.called == mock_redis_expire.called == mock_redis_set.called
        assert mock_send.called is False

    def test_it_should_fail_when_token_is_invalid(self, mock_send,
                                                  mock_redis_expire,
                                                  mock_redis_set, init_db,
                                                  client):
        client.set_cookie('/', 'token', 'some-invalid-token')
        response = client.post(RESEND_EMAIL_ENDPOINT,
                               content_type="application/json")
        assert_when_token_is_invalid(response)
        assert mock_send.called == mock_redis_expire.called == mock_redis_set.called
        assert mock_send.called is False


@patch('api.services.redis_util.RedisUtil.REDIS.set', autospec=True)
@patch('api.services.redis_util.RedisUtil.REDIS.get', autospec=True)
@patch('api.services.redis_util.RedisUtil.REDIS.delete', autospec=True)
@patch('api.services.redis_util.RedisUtil.REDIS.expire', autospec=True)
class TestConfirmResetPassword:
    def test_user_should_be_able_to_reset_their_password_once_reset_token_is_provided(
            self, mock_expire, mock_delete, mock_get, mock_set, init_db,
            client):
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user, token_type=RESET_TOKEN)
        mock_get.return_value = token
        new_password = 'some-very-new-password'
        mock_reset_id = 'mock_id'
        valid_data = json.dumps({
            'password': new_password,
            'resetId': mock_reset_id
        })
        response = client.patch(CONFIRM_RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json")
        response_body = json.loads(response.data)
        user = User.query.get(user.id)
        assert mock_get.call_count == 1
        assert mock_delete.call_count == 1
        assert mock_expire.called is False
        reset_key = mock_get.call_args[0][0]
        assert mock_delete.call_args[0][0] == reset_key
        assert reset_key == mock_reset_id
        assert user.verify_password(new_password)
        assert response.status_code == 200
        assert response_body['message'] == PASSWORD_CHANGED

    def test_error_message_should_be_sent_when_password_is_not_provided(
            self, mock_expire, mock_delete, mock_get, mock_set, init_db,
            client):
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user, token_type=RESET_TOKEN)
        valid_data = json.dumps({})
        response = client.patch(CONFIRM_RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json",
                                headers={'Authorization': f'Bearer {token}'})
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert mock_expire.called == mock_delete.called == mock_get.called == mock_set.called
        assert mock_set.called is False
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['resetId'][0] == serialization_error[
            'required']
        assert response_body['errors']['password'][0] == serialization_error[
            'required']

    def test_should_fail_with_appropriate_message_when_reset_id_is_invalid(
            self, mock_expire, mock_delete, mock_get, mock_set, init_db,
            client):
        mock_get.return_value = None
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

        assert mock_get.call_count == 1
        assert mock_delete.call_count == 0
        assert not mock_expire.called
        assert mock_set.called is False

    def test_should_fail_with_appropriate_message_when_token_is_expired(
            self, mock_expire, mock_delete, mock_get, mock_set, init_db,
            client):
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user,
                                             token_type=RESET_TOKEN,
                                             seconds=-40)
        mock_get.return_value = token
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

        assert mock_get.call_count == 1
        assert mock_delete.call_count == 1
        assert not mock_expire.called
        assert mock_set.called is False
        assert mock_delete.call_args[0][0] == reset_id


@patch('api.services.redis_util.RedisUtil.REDIS.set', autospec=True)
@patch('api.services.redis_util.RedisUtil.REDIS.expire', autospec=True)
@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestResetPassword:
    def test_user_should_be_able_to_make_reset_request_when_account_exists(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
        from api.utils.emails import EmailUtil
        EmailUtil.send_mail_as_html.delay = Mock(
            side_effect=EmailUtil.send_mail_as_html)
        user = UserGenerator.generate_model_obj(save=True)
        redirect_url = fake.url()
        valid_data = json.dumps({
            'email': user.email,
            'redirectURL': redirect_url,
        })
        response = client.patch(RESET_PASSWORD_ENDPOINT,
                                data=valid_data,
                                content_type="application/json")

        assert EmailUtil.send_mail_as_html.delay.called
        assert mock_redis_set.call_count == mock_redis_expire.called == 1
        html_to_check_for = '<h1>Reset Account</h1>'
        assert_successful_response(response,
                                   RESET_PASS_MAIL.format(user.email))
        html_content = assert_send_grid_mock_send(mock_send, user.email)

        # Extracting token from HTML content
        set_key, token = mock_redis_set.call_args[0]
        reset_id, exp_duration = mock_redis_expire.call_args[0]
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
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        assert mock_redis_expire.called == mock_redis_set.called == mock_send.called

    def test_should_fail_when_redirect_url_is_not_provided(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        assert mock_redis_expire.called == mock_redis_set.called == mock_send.called


@patch('api.services.redis_util.RedisUtil.REDIS.set', autospec=True)
@patch('api.services.redis_util.RedisUtil.REDIS.expire', autospec=True)
@patch('api.utils.emails.EmailUtil.SEND_CLIENT.send', autospec=True)
class TestRegisterEndpoint:
    def test_new_user_should_register_successfully_when_valid_data_is_provided_and_should_be_added_to_the_db(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
        from api.utils.emails import EmailUtil
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
        assert mock_redis_set.called == mock_redis_expire.called
        assert mock_redis_set.called is True
        key, token = mock_redis_set.call_args[0]
        exp_key, exp_time = mock_redis_expire.call_args[0]

        assert key == exp_key
        assert exp_time == 14.5 * 60
        assert token
        assert_reg_confirm_email_was_sent_properly(
            html_content, valid_user_dict['redirectURL'], user, token, key)

    def test_attempt_to_register_user_with_invalid_data_should_fail(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        assert mock_send.called == mock_redis_set.called == mock_redis_expire.called

    def test_attempt_to_register_user_with_first_name_or_last_name_gt_20_should_fail(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        assert mock_send.called == mock_redis_set.called == mock_redis_expire.called

    def test_attempt_to_register_user_with_first_name_or_last_name_lt_3_chars_should_fail(
            self, mock_send, mock_redis_expire, mock_redis_set, init_db,
            client):
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
        assert mock_send.called == mock_redis_set.called == mock_redis_expire.called

    def test_attempt_to_register_a_user_with_existing_email_should_fail(
            self, mock_send, mock_redis_set, mock_redis_expire, init_db,
            client):
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
        assert mock_send.called == mock_redis_set.called == mock_redis_expire.called
