from unittest.mock import Mock, patch
from api.models import Membership, Organisation, Role, db
from api.utils.error_messages import serialization_error, model_operations
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from .mocks.redis import RedisMock
from .assertions import assert_unverified_user, assert_paginator_data_values, add_cookie_to_client
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
        add_cookie_to_client(client, user, token)
        response = client.post(CREATE_ORG_URL,
                               data=valid_data,
                               content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['logo'][0] == "Field may not be null."
        assert serialization_error['invalid_field_data'] == response_body[
            'message']

    def test_should_fail_when_the_website_already_exists(
        self, mock_destroy, mock_upload, app, init_db, client):
        from api.services.file_uploader import FileUploader
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        RedisMock.flush_all()
        mock_upload.return_value = CLOUDINARY_RES
        org = OrganisationGenerator.generate_model_obj(save=True)
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        valid_data['website'] = org.website
        add_cookie_to_client(client, user, token)
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['logo'] = file
            response = client.post(CREATE_ORG_URL,
                                   data=valid_data,
                                   content_type="multipart/form-data")
        response_body = json.loads(response.data)
        assert response.status_code == 409
        assert response_body['message'] == serialization_error[
            'already_exists'].format('Website')

    def test_should_fail_with_appropriate_message_when_some_data_is_missing(
        self, mock_destroy, mock_upload, init_db, client):
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)

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
        RedisMock.flush_all()
        mock_upload.side_effect = Exception
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)

        add_cookie_to_client(client, user, token)
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
        owner_role = Role.query.filter_by(name='OWNER').first().id
        assert RedisMock.get('ROLE_OWNER') == owner_role

    def test_should_fail_when_the_user_token_has_not_been_verified(
        self, mock_destroy, mock_upload, app, init_db, client):
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user)
        assert_unverified_user(client,
                               token,
                               CREATE_ORG_URL,
                               method='post',
                               data=valid_data,
                               user=user)

    def test_save_org_should_fail_when_the_user_id_is_not_found(
        self, mock_destroy, mock_upload, app, init_db, client):
        from api.services.file_uploader import FileUploader
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        RedisMock.flush_all()
        mock_upload.return_value = CLOUDINARY_RES
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=False)
        user.id = 'unknown_id'
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['logo'] = file
            response = client.post(CREATE_ORG_URL,
                                   data=valid_data,
                                   content_type="multipart/form-data")
        response_body = json.loads(response.data)
        # Asserting response object
        assert response.status_code == 404
        assert response_body['status'] == 'error'
        assert response_body['message'] == model_operations['ids_not_found']
        assert not FileUploader.upload_file.delay.called
        assert not mock_upload.called

    def test_organisation_should_be_created_successfully_and_image_asynchronously_updated_when_input_data_is_valid(
        self, mock_destroy, mock_upload, app, init_db, client):
        from api.services.file_uploader import FileUploader
        FileUploader.upload_file.delay = Mock(
            side_effect=FileUploader.upload_file)
        RedisMock.flush_all()
        mock_upload.return_value = CLOUDINARY_RES
        valid_data = OrganisationGenerator.generate_api_input_data()
        user = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        with open('tests/mocks/org_image.jpg', 'rb') as file:
            valid_data['logo'] = file
            response = client.post(CREATE_ORG_URL,
                                   data=valid_data,
                                   content_type="multipart/form-data")
        response_body = json.loads(response.data)
        owner_role = Role.query.filter_by(name='OWNER').first().id
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
        assert membership.role.id == owner_role
        assert RedisMock.get('ROLE_OWNER') == owner_role


class TestRetrieveUserOrganisation:
    def create_test_precondition(self, saved_org_and_user_generator,
                                 num_of_orgs):
        RedisMock.flush_all()
        Membership.query.delete()
        Organisation.query.delete()
        db.session.commit()
        creator, org = saved_org_and_user_generator
        orgs_dict = []
        for i in range(1, num_of_orgs + 1):
            orgs_dict.append(
                dict(creator_id=creator.id,
                     display_name=f'Org{i}',
                     name=f'Organisation {i}',
                     website=f'some-url{i}.com',
                     address=f'{i}, My Home '))
        org_objs = Organisation.bulk_create(orgs_dict)
        return org_objs, creator, org

    def test_should_retrieve_user_organisations(self, init_db, client,
                                                saved_org_and_user_generator):
        org_objs, creator, org = self.create_test_precondition(
            saved_org_and_user_generator, 3)

        user = UserGenerator.generate_model_obj(save=True)
        memberships = []
        role_id = Role.query.filter_by(name='REGULAR USERS').one().id
        for org in org_objs:
            memberships.append(
                Membership(
                    organisation_id=org.id,
                    user_id=user.id,
                    role_id=role_id,
                ))
        Membership.bulk_create(memberships)

        token = UserGenerator.generate_token(user)
        assert_paginator_data_values(
            user=user,
            created_objs=org_objs,
            client=client,
            token=token,
            url=RETRIEVE_USER_ORGANISATIONS,
            success_msg=RETRIEVED.format('organisations'),
            current_page=1,
            total_objects=len(org_objs),
            max_objects_per_page=10,
            total_pages=math.ceil(len(org_objs) / 10),
            next_page=None,
            prev_page=None,
        )

    def test_should_return_empty_array_when_no_membership_is_found(
        self, init_db, client, saved_org_and_user_generator):
        self.create_test_precondition(saved_org_and_user_generator, 5)
        user = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user)

        assert_paginator_data_values(
            user=user,
            created_objs=[],
            client=client,
            token=token,
            url=RETRIEVE_USER_ORGANISATIONS,
            success_msg=RETRIEVED.format('organisations'),
            current_page=1,
            total_objects=0,
            max_objects_per_page=10,
            total_pages=0,
            next_page=None,
            prev_page=None,
        )
