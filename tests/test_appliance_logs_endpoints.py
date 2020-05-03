import json
from datetime import datetime, date
import pandas as pd
from tests.assertions import (add_cookie_to_client,
                              assert_user_not_in_organisation,
                              assert_user_does_not_have_permission,
                              assert_paginator_data_values,
                              assert_unverified_user)
from api.models import Log, LogValue, db, Parameter, Unit
from api.utils.success_messages import (SAVED, RETRIEVED)
from api.utils.error_messages import serialization_error

from tests.mocks.user import UserGenerator
from tests.mocks.paramter import ParameterGenerator
from io import StringIO

URL = '/api/org/{}/logs'
EXPORT_LOGS = '/api/org/{}/appliances/{}/export-logs'


def run_test_precondition(client, user_obj):
    token = UserGenerator.generate_token(user_obj)
    return add_cookie_to_client(client, user_obj, token)


class TestAddLogToApplianceEndpoint:
    def generate_json_data(self,
                           client,
                           user_obj,
                           params,
                           appliance,
                           func=None):
        client = run_test_precondition(client, user_obj)
        log_data = {}
        for index, param in enumerate(params):
            log_data[param.id] = index * 50
            if func:
                log_data[param.id] = func(index, param)

        json_data = {'logData': log_data, 'applianceId': appliance.id}
        return client, json_data

    def test_engineers_should_be_able_to_add_an_appliance_log(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            num_of_numeric_units=4)

        client, json_data = self.generate_json_data(client, user_obj,
                                                    numeric_params, appliance)
        url = URL.format(org.id)
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
                                                    numeric_params, appliance)
        url = URL.format(org.id)
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
        json_data = {
            'logData': {
                param_not_included.id: 50
            },
            'applianceId': appliance.id
        }
        url = URL.format(org.id)

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
        url = URL.format(org_1.id)
        client, json_data = self.generate_json_data(client, engineer_obj,
                                                    numeric_params_1,
                                                    appliance_1)

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert_user_not_in_organisation(response)

    def test_should_error_when_a_string_value_is_added_to_a_numeric_parameter(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=3)
        client, json_data = self.generate_json_data(
            client, user_obj, numeric_params, appliance,
            lambda idx, param: f'name_{idx}')
        url = URL.format(org.id)

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
                                                    numeric_params[1:],
                                                    appliance)
        url = URL.format(org.id)

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
                                                    numeric_params, appliance)
        url = URL.format(org.id)
        json_data['applianceId'] = 'invalid_id'

        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'not_found'].format('Appliance')
        assert response.status_code == 400
        assert response_body['status'] == 'error'


class TestExportLogsToCSVFile:
    def test_should_return_a_404_error_when_the_log_is_not_found(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = EXPORT_LOGS.format(org.id, appliance_model.id)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Logs with specified filters')

    def test_should_return_a_csv_file_when_logs_exists_for_the_specified_filters(
            self, init_db, client, saved_appliance_generator,
            saved_logs_generator):
        org, user_obj, numeric_params, _, appliance_model = saved_appliance_generator(
            'ENGINEER', num_of_numeric_units=4)
        value_mapper = {}
        param_values_by_name = {}

        # Trying to simulate the user  logging different params
        for index, param in enumerate(numeric_params):
            param = Parameter.query.get(param.id)
            param.name = f'Parameter {index}'
            value_mapper[param.id] = index * 90
            param_values_by_name[param.name] = [index * 90, param.unit.symbol]

        db.session.commit()
        saved_logs_generator(appliance_model,
                             numeric_params,
                             4,
                             value_mapper=value_mapper)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = EXPORT_LOGS.format(org.id, appliance_model.id)
        response = client.get(url)

        #  Reading the CSV and converting to a pandas Dataframe
        string_io = StringIO(response.data.decode('utf-8'))
        df = pd.read_csv(string_io)
        assert response.status_code == 200
        for param_name, param_args in param_values_by_name.items():
            param_value, param_symbol = param_args
            assert (df[param_name] == f'{param_value} {param_symbol}').all()

    def test_should_export_data_within_the_specified_dates(
            self, init_db, client, saved_appliance_generator,
            saved_logs_generator):
        org, user_obj, numeric_params, _, appliance_model = saved_appliance_generator(
            'ENGINEER', num_of_numeric_units=4)
        value_mapper = {}
        param_values_by_name = {}

        # Trying to simulate the user  logging different params
        for index, param in enumerate(numeric_params):
            param = Parameter.query.get(param.id)
            param.name = f'Parameter {index}'
            value_mapper[param.id] = index * 90
            param_values_by_name[param.name] = [index * 90, param.unit.symbol]

        db.session.commit()
        log_datetimes = [
            date(2019, 1, 1),
            date(2019, 5, 1),
            date(2019, 9, 1),
            date(2020, 1, 1)
        ]
        saved_logs_generator(appliance_model,
                             numeric_params,
                             4,
                             value_mapper=value_mapper,
                             log_datetimes=log_datetimes)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = EXPORT_LOGS.format(org.id, appliance_model.id)

        # Although there are 4 logs I'm trying to export only the ones wiithin
        url = f'{url}?start_date=2019-09-01&end_date=2020-01-01'
        response = client.get(url)

        #  Reading the CSV and converting to a pandas Dataframe
        string_io = StringIO(response.data.decode('utf-8'))
        df = pd.read_csv(string_io)
        assert response.status_code == 200
        for param_name, param_args in param_values_by_name.items():
            param_value, param_symbol = param_args
            assert (df[param_name] == f'{param_value} {param_symbol}').all()
        assert len(df) == 2


class TestRetrieveLogsEndpoint:
    def test_permitted_user_should_be_able_to_retrieve_logs(
            self, init_db, client, saved_appliance_generator,
            saved_logs_generator):
        TOTAL_LOGS = 4
        org, user_obj, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        params = numeric_params + text_params

        value_mapper = {
            numeric_param.id: index * 90
            for index, numeric_param in enumerate(numeric_params)
        }
        for text_param in text_params:
            value_mapper[text_param.id] = 'This is a sample text log'
        created_logs = saved_logs_generator(appliance_model,
                                            params,
                                            TOTAL_LOGS,
                                            value_mapper=value_mapper)

        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        created_params = numeric_params + text_params

        url = URL.format(org.id)
        url = f'{url}?appliance_id_search={appliance_model.id}'

        response_body = assert_paginator_data_values(
            user=user_obj,
            created_objs=created_params,
            client=client,
            token=token,
            url=url,
            success_msg=RETRIEVED.format('Logs'),
            current_page=1,
            total_objects=TOTAL_LOGS,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )
        # import pdb; pdb.set_trace()
        logs_id_mapper = {param.id: param for param in created_logs}

        for retrieved_log in response_body['data']:
            log_model = logs_id_mapper.get(retrieved_log['id'])
            assert log_model is not None
            for log_value in log_model.log_values:
                assert str(value_mapper.get(
                    log_value.parameter_id)) == log_value.value

    def test_should_search_only_by_retrieved_appliacne_id_when_the_appliance_id_search_is_specified(
            self, init_db, client, saved_appliance_generator,
            saved_logs_generator):
        TOTAL_LOGS_FOR_EACH_APPLIANCE = 4
        org, user_obj, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        #  This would add logs for appliance model 2 in the same organisation
        org, _, _, _, appliance_model2 = saved_appliance_generator('ENGINEER',
                                                                   3,
                                                                   3,
                                                                   org=org)
        params = numeric_params + text_params

        #  Creates logs for both appliances
        saved_logs_generator(appliance_model, params,
                             TOTAL_LOGS_FOR_EACH_APPLIANCE)
        saved_logs_generator(appliance_model2, params,
                             TOTAL_LOGS_FOR_EACH_APPLIANCE)

        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        created_params = numeric_params + text_params
        url = URL.format(org.id)
        url = f'{url}?appliance_id_search={appliance_model.id}'

        #  This queries the API for appliance one and checks that it has the correct number of appliances
        assert_paginator_data_values(
            user=user_obj,
            created_objs=created_params,
            client=client,
            token=token,
            url=url,
            success_msg=RETRIEVED.format('Logs'),
            current_page=1,
            total_objects=TOTAL_LOGS_FOR_EACH_APPLIANCE,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

        # Checks that the Log has more that 8 logs
        assert Log.query.filter_by(organisation_id=org.id).count(
        ) == TOTAL_LOGS_FOR_EACH_APPLIANCE * 2
        assert LogValue.query.join(
            Log, (Log.id == LogValue.log_id) & (Log.organisation_id == org.id)
        ).count() == 2 * TOTAL_LOGS_FOR_EACH_APPLIANCE * len(params)

    def test_should_retrieve_the_most_recently_lgged_for_all_appliances_when_no_search_is_specified(
            self, init_db, client, saved_appliance_generator,
            saved_logs_generator):
        TOTAL_LOGS_FOR_EACH_APPLIANCE = 4
        org, user_obj, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        #  This would add logs for appliance model 2 in the same organisation
        org, _, _, _, appliance_model2 = saved_appliance_generator('ENGINEER',
                                                                   3,
                                                                   3,
                                                                   org=org)
        params = numeric_params + text_params

        #  Creates logs for both appliances
        saved_logs_generator(appliance_model, params,
                             TOTAL_LOGS_FOR_EACH_APPLIANCE)
        saved_logs_generator(appliance_model2, params,
                             TOTAL_LOGS_FOR_EACH_APPLIANCE)

        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        created_params = numeric_params + text_params
        url = URL.format(org.id)

        #  This queries the API for appliance one and checks that it has the correct number of appliances
        assert_paginator_data_values(
            user=user_obj,
            created_objs=created_params,
            client=client,
            token=token,
            url=url,
            success_msg=RETRIEVED.format('Logs'),
            current_page=1,
            total_objects=TOTAL_LOGS_FOR_EACH_APPLIANCE * 2,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

        # Checks that the Log has more that 8 logs
        assert Log.query.filter_by(organisation_id=org.id).count(
        ) == 2 * TOTAL_LOGS_FOR_EACH_APPLIANCE
        assert LogValue.query.join(
            Log, (Log.id == LogValue.log_id) & (Log.organisation_id == org.id)
        ).count() == 2 * TOTAL_LOGS_FOR_EACH_APPLIANCE * len(params)

    def test_should_fail_when_user_is_not_verified(self, init_db, client,
                                                   saved_appliance_generator):
        org, _, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        user_obj = UserGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = URL.format(org.id)
        assert_unverified_user(client, token, url, user=user_obj)

    def test_should_fail_when_the_user_is_not_part_of_org(
            self, init_db, client, saved_appliance_generator):
        org, _, numeric_params, text_params, appliance_model = saved_appliance_generator(
            'ENGINEER', 3, 3)
        user_obj = UserGenerator.generate_model_obj(verified=True, save=True)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        url = URL.format(org.id)
        response = client.get(url)
        assert_user_not_in_organisation(response)
