import json
from tests.assertions import add_cookie_to_client, assert_user_not_in_organisation, assert_user_does_not_have_permission
from api.utils.helper_functions import capitalize_each_word_in_sentence
from api.utils.success_messages import (SAVED)
from api.utils.error_messages import serialization_error

from tests.mocks.user import UserGenerator
from tests.mocks.paramter import ParameterGenerator
URL = '/api/org/{}/appliances/{}/logs'


def run_test_precondition(client, user_obj):
    token = UserGenerator.generate_token(user_obj)
    return add_cookie_to_client(client, user_obj, token)


class TestAddLogToApplianceEndpoint:
    def generate_json_data(self, client, user_obj, params, func=None):
        client = run_test_precondition(client, user_obj)
        json_data = {}
        for index, param in enumerate(params):
            json_data[param.id] = index * 50
            if func:
                json_data[param.id] = func(index, param)
        return client, json_data

    def test_engineers_should_be_able_to_add_an_appliance_log(
        self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            num_of_numeric_units=4)

        client, json_data = self.generate_json_data(client, user_obj,
                                                    numeric_params)
        url = URL.format(org.id, appliance.id)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == SAVED.format('Log')
        assert response.status_code == 201
        assert 'data' in response_body
        assert response_body['status'] == 'success'

    def test_regular_users_should_not_be_able_to_add_logs_for_an_appliance(
        self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='REGULAR USERS', num_of_numeric_units=4)
        client, json_data = self.generate_json_data(client, user_obj,
                                                    numeric_params)
        url = URL.format(org.id, appliance.id)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert_user_does_not_have_permission(response)

    def test_engineers_should_not_be_able_to_create_logs_for_params_that_are_not_in_appliance(
        self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=1)
        param_not_included = ParameterGenerator.generate_model_obj(
            organisation_id=org.id)
        client = run_test_precondition(client, user_obj)
        json_data = {param_not_included.id: 50}
        url = URL.format(org.id, appliance.id)

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'

        assert len(response_body['errors']) == 1
        assert response_body['errors'][
            numeric_params[0].id] == serialization_error['required']

    def test_engineer_should_not_be_able_to_add_log_for_appliance_that_is_not_in_a_diff_organisation(
        self, init_db, client, saved_appliance_generator):
        org_1, _, numeric_params_1, _, appliance_1 = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=1)
        org_2, engineer_obj, _, _, appliance_2 = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=1)

        #  Trying to simulate an engineer in org_2 trying to log params for org_1
        url = URL.format(org_1.id, appliance_1.id)
        client, json_data = self.generate_json_data(client, engineer_obj,
                                                    numeric_params_1)

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert_user_not_in_organisation(response)

    def test_should_error_when_a_string_value_is_added_to_a_numeric_parameter(
        self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=3)
        client, json_data = self.generate_json_data(
            client, user_obj, numeric_params, lambda idx, param: f'name_{idx}')
        url = URL.format(org.id, appliance.id)

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response.status_code == 400
        assert 'data' not in response_body
        assert response_body['status'] == 'error'

        assert len(response_body['errors']) == 3
        for param in numeric_params:
            assert response_body['errors'][
                param.id] == serialization_error['number_only']

    def test_should_error_when_a_particular_log_value_is_missing(
        self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            num_of_numeric_units=4)
        client, json_data = self.generate_json_data(client, user_obj,
                                                    numeric_params[1:])
        url = URL.format(org.id, appliance.id)

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response.status_code == 400
        assert response_body['errors'][
            numeric_params[0].id] == serialization_error['required']
        assert response_body['status'] == 'error'

    def test_should_return_error_when_appliance_id_was_not_found(
        self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            num_of_numeric_units=4)
        client, json_data = self.generate_json_data(client, user_obj,
                                                    numeric_params)
        url = URL.format(org.id, 'invalid_id')

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'not_found'].format('Appliance')
        assert response.status_code == 400
        assert response_body['status'] == 'error'
