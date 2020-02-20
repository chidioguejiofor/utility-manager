from tests.assertions import add_cookie_to_client
from api.utils.success_messages import (CREATED)
from api.utils.error_messages import serialization_error, authentication_errors
from api.models import ApplianceCategory, db
from tests.mocks.user import UserGenerator
from tests.mocks.organisation import OrganisationGenerator
from tests.mocks.appliance_category import ApplianceCategoryGenerator

import json

CREATE_URL = '/api/org/{}/appliance-category'


class TestCreateApplianceCategoryEndpoint:
    def run_test_precondition(self):
        ApplianceCategory.query.delete()
        db.session.commit()

    def test_appliance_category_should_be_created_when_user_is_an_admin_in_the_organisation(
            self, init_db, client):
        self.run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 201
        response_body = json.loads(response.data)
        assert response_body['message'] == CREATED.format('Appliance Category')
        assert 'data' in response_body
        assert response_body['status'] == 'success'

        model = ApplianceCategory.query.get(response_body['data']['id'])
        assert model.name == category_data['name'].capitalize()
        assert model.description == category_data['description']
        assert model.created_by_id == org.creator.id
        assert model.updated_by_id is None

    def test_should_fail_when_the_appliance_category_already_exists(
            self, client, init_db):
        self.run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 201
        category_data['name'] = category_data['name'].upper()
        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 409
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'exists_in_org'].format('Appliance Category')

    def test_should_fail_when_the_body_is_empty(self, client, init_db):
        self.run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps({}),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert len(response_body['errors']['name']) > 0
        assert len(response_body['errors']['description']) > 0

    def test_should_return_404_when_user_is_not_part_of_org(
            self, init_db, client):
        self.run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')
        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_an_admin(
            self, init_db, client, add_user_to_organisation):
        self.run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        add_user_to_organisation(org, user, role='ENGINEER')

        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)

        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors['forbidden']
        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_verified(
            self, init_db, client, add_user_to_organisation):
        self.run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        user = UserGenerator.generate_model_obj(save=True, verified=False)
        add_user_to_organisation(org, user, role='ENGINEER')

        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)

        response = client.post(CREATE_URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors[
            'unverified_user']
        assert response_body['status'] == 'error'
