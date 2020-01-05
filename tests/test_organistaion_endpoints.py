from unittest.mock import Mock, patch
from api.models import Membership, RoleEnum, Organisation
from api.utils.error_messages import serialization_error, authentication_errors
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from .assertions import assert_paginator_meta
import math
import json
from api.utils.success_messages import RETRIEVED

CREATE_ORG_URL = '/api/org/create'
RETRIEVE_USER_ORGANISATIONS = '/api/user/orgs'
CLOUDINARY_RES = {
    'public_id': 'mock-public-id',
    'secure_url': 'http://host/some-image-url.png'
}


@patch('cloudinary.uploader.upload', autospec=True)
@patch('cloudinary.uploader.destroy', autospec=True)
class TestCreateOrganisation:
    def test_should_fail_when_logo_is_missing(self, mock_destroy, mock_upload,
                                              init_db, client):
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.post(CREATE_ORG_URL,
                               data=valid_data,
                               content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['logo'][0] == "Field may not be null."
        assert serialization_error['invalid_field_data'] == response_body[
            'message']

    def test_should_fail_when_the_website_already_exists(
            self, mock_destroy, mock_upload, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        valid_data['website'] = org.website
        client.set_cookie('/', 'token', token)
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['logo'] = file
            response = client.post(CREATE_ORG_URL,
                                   data=valid_data,
                                   content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 409
        assert response_body['message'] == serialization_error[
            'already_exists'].format('`website`')

    def test_should_fail_with_appropriate_message_when_some_data_is_missing(
            self, mock_destroy, mock_upload, init_db, client):
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)

        response = client.post(CREATE_ORG_URL,
                               data={},
                               content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert serialization_error['required'] == response_body['errors'][
            'address'][0]
        assert serialization_error['required'] == response_body['errors'][
            'website'][0]
        assert serialization_error['required'] == response_body['errors'][
            'displayName'][0]
        assert serialization_error['invalid_field_data'] == response_body[
            'message']

    def test_should_not_update_model_image_when_cloudinary_throws_error(
            self, mock_destroy, mock_upload, app, init_db, client):
        from api.services.file_uploader import FileUploader
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        mock_upload.side_effect = Exception
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['logo'] = file
            response = client.post(CREATE_ORG_URL,
                                   data=valid_data,
                                   content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 201
        assert FileUploader.upload_file.delay.called
        assert response_body['data']['logoUrl'] == None
        assert 'id' in response_body['data']
        assert response_body['data']['subscriptionType'] == "FREE"
        assert response_body['data']['creator']['email'] == user.email
        assert response_body['data']['creator']['id'] == user.id
        assert mock_upload.called

    def test_should_fail_when_the_user_token_has_not_been_verified(
            self, mock_destroy, mock_upload, app, init_db, client):
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user)
        client.set_cookie('/', 'token', token)
        response = client.post(CREATE_ORG_URL,
                               data=valid_data,
                               content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 403
        assert authentication_errors['unverified_user'] == response_body[
            'message']

    def test_organisation_should_be_created_successfully_and_image_asynchronously_updated_when_input_data_is_valid(
            self, mock_destroy, mock_upload, app, init_db, client):
        from api.services.file_uploader import FileUploader
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        mock_upload.return_value = CLOUDINARY_RES
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['logo'] = file
            response = client.post(CREATE_ORG_URL,
                                   data=valid_data,
                                   content_type="multipart/form-data")
        response_body = json.loads(response.data)
        # Asserting response object
        assert response.status_code == 201
        assert FileUploader.upload_file.delay.called
        assert response_body['data']['logoUrl'] == CLOUDINARY_RES['secure_url']
        assert 'id' in response_body['data']
        assert response_body['data']['subscriptionType'] == "FREE"
        assert response_body['data']['creator']['email'] == user.email
        assert response_body['data']['creator']['id'] == user.id
        assert mock_upload.called

        # A new membership should be created with that user
        memberships = Membership.query.filter_by(
            organisation_id=response_body['data']['id'],
            user_id=user.id,
        )
        membership = memberships.first()
        assert memberships.count() == 1
        assert membership.role == RoleEnum.OWNER


class TestRetrieveUserOrganisation:
    def test_should_retrieve_user_organisations(self, init_db, client,
                                                saved_org_and_user_generator):
        creator, org = saved_org_and_user_generator
        orgs_dict = [
            dict(creator_id=creator.id,
                 display_name='Org1',
                 name='Organisation Un',
                 website='some-url.com',
                 address='My Home'),
            dict(creator_id=creator.id,
                 display_name='Org2',
                 name='Organisation Deux',
                 website='some-url2.com',
                 address='My Home'),
            dict(creator_id=creator.id,
                 display_name='Org3',
                 name='Organisation Tres',
                 website='some-url3.com',
                 address='My Home'),
        ]
        Organisation.bulk_create(orgs_dict)
        user = UserGenerator.generate_model_obj(save=True)
        memberships = []
        display_names = Organisation.display_name.in_(['Org1', 'Org2', 'Org3'])
        for org in Organisation.query.filter(display_names).all():
            memberships.append(
                Membership(
                    organisation_id=org.id,
                    user_id=user.id,
                ))
        Membership.bulk_create(memberships)

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(RETRIEVE_USER_ORGANISATIONS,
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('organisations')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(orgs_dict),
            max_objects_per_page=10,
            total_pages=math.ceil(len(orgs_dict) / 10),
            next_page=None,
            prev_page=None,
        )

    def test_should_return_empty_array_when_no_membership_is_found(
            self, init_db, client, saved_org_and_user_generator):
        creator, org = saved_org_and_user_generator
        orgs_dict = [
            dict(creator_id=creator.id,
                 display_name='Org5',
                 name='Organisation Un',
                 website='some-url5.com',
                 address='My Home'),
            dict(creator_id=creator.id,
                 display_name='Org6',
                 name='Organisation Deux',
                 website='some-url6.com',
                 address='My Home'),
            dict(creator_id=creator.id,
                 display_name='Org7',
                 name='Organisation Tres',
                 website='some-url7.com',
                 address='My Home'),
        ]
        Organisation.bulk_create(orgs_dict)
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(RETRIEVE_USER_ORGANISATIONS,
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('organisations')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=0,
            max_objects_per_page=10,
            total_pages=0,
            next_page=None,
            prev_page=None,
        )
