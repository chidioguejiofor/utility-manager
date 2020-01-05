from unittest.mock import Mock, patch
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from .assertions import assert_when_token_is_missing, assert_when_token_is_invalid
import math
import json
from api.utils.success_messages import RETRIEVED, UPDATED
from api.utils.error_messages import serialization_error

PROFILE_URL = '/api/user/profile'
RETRIEVE_USER_ORGANISATIONS = '/api/user/orgs'
CLOUDINARY_RES = {
    'public_id': 'mock-public-id',
    'secure_url': 'http://host/some-user-image-url.png',
}


class TestGetProfile:
    def test_when_token_is_valid_user_profile_should_be_retrieved(
            self, init_db, client):

        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(PROFILE_URL, content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Profile')
        assert response_body['status'] == 'success'
        assert response_body['data']['firstName'] == user.first_name
        assert response_body['data']['lastName'] == user.last_name
        assert response_body['data']['username'] == user.username
        assert response_body['data']['imageURL'] == user.image_url
        assert response_body['data']['verified'] == user.verified

    def test_should_succeed_when_user_has_not_verified_his_account(
            self, init_db, client):
        user = UserGenerator.generate_model_obj(verified=False, save=True)
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(PROFILE_URL, content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Profile')
        assert response_body['status'] == 'success'
        assert response_body['data']['firstName'] == user.first_name
        assert response_body['data']['lastName'] == user.last_name
        assert response_body['data']['username'] == user.username
        assert response_body['data']['verified'] == user.verified
        assert response_body['data']['imageURL'] == user.image_url

    def test_should_return_appropriate_message_when_token_is_invalid(
            self, init_db, client, saved_org_and_user_generator):
        client.set_cookie('/', 'token', 'invalid_token')
        response = client.get(PROFILE_URL, content_type="application/json")

        assert_when_token_is_invalid(response)

    def test_return_appropriate_message_when_token_is_missing(
            self, init_db, client):
        response = client.get(PROFILE_URL, content_type="application/json")

        assert_when_token_is_missing(response)


@patch('cloudinary.uploader.upload', autospec=True)
@patch('cloudinary.uploader.destroy', autospec=True)
class TestUpdateProfile:
    def test_user_can_update_all_fields(self, mock_destroy, mock_upload,
                                        init_db, client):
        from api.services.file_uploader import FileUploader
        mock_upload.return_value = CLOUDINARY_RES
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        valid_data = {
            'username': 'someNewUsername',
            'firstName': 'AbaBoy',
            'lastName': 'firstSon',
        }
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['image'] = file
            response = client.patch(PROFILE_URL,
                                    data=valid_data,
                                    content_type="multipart/form-data")

        response_body = json.loads(response.data)

        assert response.status_code == 201
        assert response_body['message'] == UPDATED.format('Profile')
        assert response_body['status'] == 'success'
        assert response_body['data']['firstName'] == valid_data['firstName']
        assert response_body['data']['lastName'] == valid_data['lastName']
        assert response_body['data']['username'] == valid_data['username']
        assert response_body['data']['imageURL'] == CLOUDINARY_RES[
            'secure_url']
        assert response_body['data']['verified'] == user.verified

        assert mock_upload.called
        assert not mock_destroy.called

        assert FileUploader.upload_file.delay.called
        assert FileUploader.upload_file.delay.call_args[0][0] == user.id
        assert FileUploader.upload_file.delay.call_args[0][1] == 'User'

    def test_destroy_previous_image_when_user_specifies_a_new_one(
            self, mock_destroy, mock_upload, init_db, client):
        from api.services.file_uploader import FileUploader
        mock_upload.return_value = CLOUDINARY_RES
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        prev_publick_id = 'some_rough-text'
        user = UserGenerator.generate_model_obj(verified=True)
        user.image_url = 'http://me.com'
        user.image_public_id = prev_publick_id
        user.save()
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        valid_data = {}
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['image'] = file
            response = client.patch(PROFILE_URL,
                                    data=valid_data,
                                    content_type="multipart/form-data")

        response_body = json.loads(response.data)

        assert response.status_code == 201
        assert response_body['message'] == UPDATED.format('Profile')
        assert response_body['status'] == 'success'
        assert response_body['data']['firstName'] == user.first_name
        assert response_body['data']['lastName'] == user.last_name
        assert response_body['data']['username'] == user.username
        assert response_body['data']['imageURL'] == CLOUDINARY_RES[
            'secure_url']
        assert response_body['data']['verified'] == user.verified

        assert mock_upload.called
        assert mock_destroy.called

        assert FileUploader.upload_file.delay.called
        assert FileUploader.upload_file.delay.call_args[0][0] == user.id
        assert FileUploader.upload_file.delay.call_args[0][1] == 'User'

        assert mock_destroy.call_args[0][0] == prev_publick_id

    def test_file_uploader_should_not_be_called_if_image_is_not_specified(
            self, mock_destroy, mock_upload, init_db, client):
        from api.services.file_uploader import FileUploader
        mock_upload.return_value = CLOUDINARY_RES
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        valid_data = {
            'username': 'someNewUsername10',
            'firstName': 'AbaBoy',
            'lastName': 'firstSon',
        }

        response = client.patch(PROFILE_URL,
                                data=valid_data,
                                content_type="multipart/form-data")

        response_body = json.loads(response.data)

        assert response.status_code == 201
        assert response_body['message'] == UPDATED.format('Profile')
        assert response_body['status'] == 'success'
        assert response_body['data']['firstName'] == valid_data['firstName']
        assert response_body['data']['lastName'] == valid_data['lastName']
        assert response_body['data']['username'] == valid_data['username']
        assert response_body['data']['imageURL'] is None
        assert response_body['data']['verified'] == user.verified

        assert not mock_upload.called
        assert not mock_destroy.called

        assert not FileUploader.upload_file.delay.called

    def test_should_update_only_specified_data(self, mock_destroy, mock_upload,
                                               init_db, client):
        from api.services.file_uploader import FileUploader
        mock_upload.return_value = CLOUDINARY_RES
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        valid_data = {
            'username': 'me101Awesome',
        }

        response = client.patch(PROFILE_URL,
                                data=valid_data,
                                content_type="multipart/form-data")

        response_body = json.loads(response.data)

        assert response.status_code == 201
        assert response_body['message'] == UPDATED.format('Profile')
        assert response_body['status'] == 'success'
        assert response_body['data']['firstName'] == user.first_name
        assert response_body['data']['lastName'] == user.last_name
        assert response_body['data']['username'] == valid_data['username']
        assert response_body['data']['imageURL'] is None
        assert response_body['data']['verified'] == user.verified

        assert not mock_upload.called
        assert not mock_destroy.called

        assert not FileUploader.upload_file.delay.called

    def test_should_return_bad_request_if_no_data_is_specified(
            self, mock_destroy, mock_upload, init_db, client):
        from api.services.file_uploader import FileUploader
        mock_upload.return_value = CLOUDINARY_RES
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)

        response = client.patch(PROFILE_URL,
                                data={},
                                content_type="multipart/form-data")

        response_body = json.loads(response.data)

        assert response.status_code == 400
        assert response_body['message'] == serialization_error[
            'empty_update_data']
        assert response_body['status'] == 'error'

        assert not mock_upload.called
        assert not mock_destroy.called

        assert not FileUploader.upload_file.delay.called

    def test_should_fail_when_new_username_already_exists(
            self, mock_destroy, mock_upload, init_db, client):
        from api.services.file_uploader import FileUploader
        mock_upload.return_value = CLOUDINARY_RES
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        user2 = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        existing_username_data = {
            'username': user2.username,
            'firstName': 'SeniorBoy'
        }
        client.set_cookie('/', 'token', token)

        response = client.patch(PROFILE_URL,
                                data=existing_username_data,
                                content_type="multipart/form-data")

        response_body = json.loads(response.data)

        assert response.status_code == 409
        assert response_body['message'] == serialization_error[
            'already_exists'].format('username')
        assert response_body['status'] == 'error'

        assert not mock_upload.called
        assert not mock_destroy.called

        assert not FileUploader.upload_file.delay.called

    def test_should_return_appropriate_message_when_token_is_invalid(
            self, mock_destroy, mock_upload, init_db, client,
            saved_org_and_user_generator):
        client.set_cookie('/', 'token', 'invalid_token')
        response = client.patch(PROFILE_URL, content_type="application/json")

        assert_when_token_is_invalid(response)

    def test_return_appropriate_message_when_token_is_missing(
            self, mock_destroy, mock_upload, init_db, client):
        response = client.patch(PROFILE_URL, content_type="application/json")

        assert_when_token_is_missing(response)
