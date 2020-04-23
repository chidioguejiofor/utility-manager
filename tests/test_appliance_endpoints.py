from tests.assertions import add_cookie_to_client
from api.utils.success_messages import (CREATED)
from api.utils.error_messages import serialization_error, authentication_errors
from api.models import ApplianceCategory, db, Appliance, ApplianceParameter, Parameter
from tests.mocks.user import UserGenerator
from tests.mocks.organisation import OrganisationGenerator
from tests.mocks.appliance_category import ApplianceCategoryGenerator
from tests.mocks.appliance import ApplianceGenerator
from tests.mocks.paramter import ParameterGenerator

import json

CREATE_URL = '/api/org/{}/appliance-category/{}/appliances'


class TestCreateApplianceEndpoints:
    def run_test_precondition(self, client, **kwargs):
        ApplianceParameter.query.delete()
        Parameter.query.delete()
        Appliance.query.delete()
        ApplianceCategory.query.delete()

        db.session.commit()
        org = OrganisationGenerator.generate_model_obj(save=True)
        category_model = ApplianceCategoryGenerator.generate_model_obj(
            org.id, save=True)
        parameter = ParameterGenerator.generate_model_obj(save=True)
        user = kwargs.get('user', org.creator)
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        return org, category_model, parameter

    def generate_json(self, parameter_id):
        return {
            "label": "Generator",
            "specs": {
                "manufacture": "Cummins",
                "rating": "500KVA",
                "plateNumber": "44220033",
            },
            "parameters": [parameter_id]
        }

    def test_appliance_should_be_created_when_user_is_an_admin_in_the_organisation(
        self, init_db, client):
        org, category_model, parameter = self.run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data([parameter.id])
        response = client.post(CREATE_URL.format(org.id, category_model.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 201
        response_body = json.loads(response.data)
        assert response_body['message'] == CREATED.format('Appliance')
        assert 'data' in response_body
        assert response_body['status'] == 'success'

        model = Appliance.query.get(response_body['data']['id'])
        assert model.label == json_data['label']
        assert model.specs == json_data['specs']
        assert model.created_by_id == org.creator.id
        assert model.updated_by_id is None
        assert ApplianceParameter.query.filter_by(
            parameter_id=parameter.id, appliance_id=model.id).count() == 1

    def test_should_fail_when_the_appliance_already_exists(
        self, client, init_db):
        org, category_model, parameter = self.run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data([parameter.id])
        response = client.post(CREATE_URL.format(org.id, category_model.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 201

        json_data['label'] = json_data['label'].upper()
        response = client.post(CREATE_URL.format(org.id, category_model.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 409
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'exists_in_org'].format('Appliance')

    def test_should_fail_when_the_body_is_empty(self, client, init_db):
        org, category_model, parameter = self.run_test_precondition(client)
        response = client.post(CREATE_URL.format(org.id, category_model.id),
                               data=json.dumps({}),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert len(response_body['errors']['label']) > 0
        assert len(response_body['errors']['specs']) > 0
        assert len(response_body['errors']['parameters']) > 0

    def test_should_return_404_when_user_is_not_part_of_org(
        self, init_db, client):
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        org, category_model, parameter = self.run_test_precondition(client,
                                                                    user=user)
        json_data = ApplianceGenerator.generate_api_input_data([parameter.id])
        response = client.post(CREATE_URL.format(org.id, 'abas'),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')
        assert response_body['status'] == 'error'

    def test_should_fail_when_there_are_invalid_parameters_in_the_request(
        self, init_db, client):
        org, category_model, parameter = self.run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data([parameter.id])
        json_data['parameters'].append('id1')
        json_data['parameters'].append('id1')
        json_data['parameters'].append('id2')
        response = client.post(CREATE_URL.format(org.id, category_model.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'some_ids_not_found'].format(f'2 parameters')
        assert response.status_code == 400

    def test_should_return_404_when_appliance_category_is_not_found(
        self, init_db, client):
        org, category_model, parameter = self.run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data([parameter.id])
        response = client.post(CREATE_URL.format(org.id, 'abas'),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'not_found'].format('Appliance Category')
        assert response.status_code == 404

        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_an_admin(
        self, init_db, client, add_user_to_organisation):
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        org, category_model, parameter = self.run_test_precondition(client,
                                                                    user=user)
        add_user_to_organisation(org, user, role='ENGINEER')
        json_data = self.generate_json(parameter.id)

        response = client.post(CREATE_URL.format(org.id, parameter.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors['forbidden']
        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_verified(
        self, init_db, client, add_user_to_organisation):
        user = UserGenerator.generate_model_obj(save=True, verified=False)
        org, category_model, parameter = self.run_test_precondition(client,
                                                                    user=user)
        add_user_to_organisation(org, user, role='ENGINEER')
        json_data = self.generate_json(parameter.id)

        response = client.post(CREATE_URL.format(org.id, category_model.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors[
            'unverified_user']
        assert response_body['status'] == 'error'
