from tests.assertions import (add_cookie_to_client,
                              assert_paginator_data_values,
                              assert_user_not_in_organisation,
                              assert_unverified_user)
from api.utils.success_messages import (CREATED, RETRIEVED)
from api.utils.error_messages import serialization_error, authentication_errors, model_operations
from api.models import ApplianceCategory, db, Appliance, ApplianceParameter, Parameter
from tests.mocks.user import UserGenerator
from tests.mocks.organisation import OrganisationGenerator
from tests.mocks.appliance_category import ApplianceCategoryGenerator
from tests.mocks.appliance import ApplianceGenerator
from tests.mocks.paramter import ParameterGenerator

import json

URL = '/api/org/{}/appliances'
SINGLE_APPLIANCE_URL = '/api/org/{}/appliances/{}'


def run_test_precondition(client, **kwargs):
    ApplianceParameter.query.delete()
    Parameter.query.delete()
    Appliance.query.delete()
    ApplianceCategory.query.delete()

    db.session.commit()
    org = OrganisationGenerator.generate_model_obj(save=True)
    category_model = ApplianceCategoryGenerator.generate_model_obj(org.id,
                                                                   save=True)
    parameter = ParameterGenerator.generate_model_obj(organisation_id=org.id,
                                                      save=True)
    user = kwargs.get('user', org.creator)
    token = UserGenerator.generate_token(user)
    add_cookie_to_client(client, user, token)
    return org, category_model, parameter


class TestCreateApplianceEndpoints:
    def test_appliance_should_be_created_when_user_is_an_admin_in_the_organisation(
            self, init_db, client):
        org, category_model, parameter = run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id)
        response = client.post(URL.format(org.id),
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

    def test_appliance_should_be_created_when_non_required_params_are_specified(
            self, init_db, client):
        org, category_model, parameter = run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id, required_params=[parameter.id])
        response = client.post(URL.format(org.id),
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
        assert ApplianceParameter.query.filter_by(parameter_id=parameter.id,
                                                  appliance_id=model.id,
                                                  required=True).count() == 1

    def test_appliance_should_fail_when_an_invalid_id_is_specified_in_required_params(
            self, init_db, client):
        org, category_model, parameter = run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id],
            category_model.id,
            required_params=[parameter.id, 'invalid'])
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors'][
            'requiredParameters'] == serialization_error[
                'invalid_required_params']

    def test_should_fail_when_the_appliance_already_exists(
            self, client, init_db):
        org, category_model, parameter = run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 201

        json_data['label'] = json_data['label'].upper()
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 409
        response_body = json.loads(response.data)
        assert response_body['message'] == model_operations[
            'appliance_already_exists']

    def test_should_fail_when_the_body_is_empty(self, client, init_db):
        org, category_model, parameter = run_test_precondition(client)
        response = client.post(URL.format(org.id),
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
        org, category_model, parameter = run_test_precondition(client,
                                                               user=user)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')
        assert response_body['status'] == 'error'

    def test_should_fail_when_there_are_invalid_parameters_in_the_request(
            self, init_db, client):
        org, category_model, parameter = run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id)
        invalid_param_ids = ['id1', 'id1', 'id2']
        json_data['parameters'].extend(invalid_param_ids)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['status'] == 'error'
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert response_body['errors']['parameter_ids'][
            'message'] == serialization_error['not_found'].format(
                'Some parameters')
        assert set(response_body['errors']['parameter_ids']
                   ['invalidValues']) == set(invalid_param_ids)
        assert response.status_code == 404

    def test_should_return_404_when_appliance_category_is_not_found(
            self, init_db, client):
        org, category_model, parameter = run_test_precondition(client)
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], 'invalid-category-id')
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert response_body['errors']['categoryId'][
            'message'] == serialization_error['not_found'].format(
                'Appliance Category')
        assert response_body['errors']['categoryId']['invalidValues'] == [
            'invalid-category-id'
        ]
        assert response.status_code == 404

        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_an_admin(
            self, init_db, client, add_user_to_organisation):
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        org, category_model, parameter = run_test_precondition(client,
                                                               user=user)
        add_user_to_organisation(org, user, role='ENGINEER')
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id)

        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors['forbidden']
        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_verified(
            self, init_db, client, add_user_to_organisation):
        user = UserGenerator.generate_model_obj(save=True, verified=False)
        org, category_model, parameter = run_test_precondition(client,
                                                               user=user)
        add_user_to_organisation(org, user, role='ENGINEER')
        json_data = ApplianceGenerator.generate_api_input_data(
            [parameter.id], category_model.id)

        response = client.post(URL.format(org.id, category_model.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors[
            'unverified_user']
        assert response_body['status'] == 'error'


class TestRetrieveApplianceParameterEndpoint:
    def test_permitted_user_should_be_able_to_retrieve_appliances(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = SINGLE_APPLIANCE_URL.format(org.id, appliance_model.id)
        created_params = numeric_params + text_params
        response_body = assert_paginator_data_values(
            user=user_obj,
            created_objs=created_params,
            client=client,
            token=token,
            url=f'{url}/parameters',
            success_msg=RETRIEVED.format('Appliance Parameters'),
            current_page=1,
            total_objects=6,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

        param_id_mapper = {param.id: param for param in created_params}

        for appliance_param in response_body['data']:
            retrieved_param = appliance_param['parameter']
            param_model = param_id_mapper.get(retrieved_param['id'])
            assert param_model is not None
            assert param_model.name == retrieved_param['name']
            assert param_model.validation == retrieved_param['validation']
            assert param_model.value_type.name == retrieved_param['valueType']
            assert appliance_param['required'] is False

    def test_should_retrieve_only_params_that_match_the_given_id(
            self, init_db, client, saved_appliance_generator):
        #  Simulating generating 2 appliances with different parameters
        org, user_obj, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        _, _, _, _, appliance_model_2 = saved_appliance_generator('ENGINEER',
                                                                  3,
                                                                  3,
                                                                  org=org)

        # Simulating generating 1 appliance in a different organisation
        saved_appliance_generator('ENGINEER', 3, 3)

        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = SINGLE_APPLIANCE_URL.format(org.id, appliance_model.id)
        created_params = numeric_params + text_params
        response_body = assert_paginator_data_values(  # this checks that only the params for appliance_one are returned
            user=user_obj,
            created_objs=created_params,
            client=client,
            token=token,
            url=f'{url}/parameters',
            success_msg=RETRIEVED.format('Appliance Parameters'),
            current_page=1,
            total_objects=6,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

        param_id_mapper = {param.id: param for param in created_params}

        for appliance_param in response_body['data']:
            retrieved_parameter = appliance_param['parameter']
            param_model = param_id_mapper.get(retrieved_parameter['id'])
            assert param_model is not None
            assert param_model.name == retrieved_parameter['name']
            assert param_model.validation == retrieved_parameter['validation']
            assert param_model.value_type.name == retrieved_parameter[
                'valueType']
            assert appliance_param['required'] is False

    def test_should_fail_when_user_is_not_verified(self, init_db, client,
                                                   saved_appliance_generator):
        org, _, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        user_obj = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = SINGLE_APPLIANCE_URL.format(org.id, appliance_model.id)
        url = f'{url}/parameters'
        assert_unverified_user(client, token, url, user=user_obj)

    def test_should_fail_when_the_user_is_not_part_of_org(
            self, init_db, client, saved_appliance_generator):
        org, _, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        user_obj = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = SINGLE_APPLIANCE_URL.format(org.id, appliance_model.id)
        response = client.get(f'{url}/parameters')
        assert_user_not_in_organisation(response)
