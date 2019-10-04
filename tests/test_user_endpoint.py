from api.utils.success_messages import CREATED, LOGIN
from api.utils.error_messages import serialization_error
from api.models import User
from .mocks.user import UserGenerator
import json

REGISTER_URL = '/api/auth/register'
LOGIN_URL = '/api/auth/login'


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


class TestRegisterEndpoint:
    def test_new_user_should_register_successfully_when_valid_data_is_provided_and_should_be_added_to_the_db(
            self, init_db, client):
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
