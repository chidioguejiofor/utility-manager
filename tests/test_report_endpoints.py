import json
from api.models import (Report, ReportSection, ReportColumn, ValueTypeEnum, db,
                        Parameter, AggregationType)

from api.utils.error_messages import serialization_error, parameter_errors, authentication_errors
from api.utils.success_messages import CREATED, RETRIEVED
from .assertions import add_cookie_to_client, assert_user_does_not_have_permission, assert_successful_response
from .mocks.report import ReportGenerator, ReportColumnGenerator, ReportSectionGenerator
from .mocks.user import UserGenerator

REPORT_URL = '/api/org/{}/reports'
REPORT_SECTION_URL = REPORT_URL + '/{}/sections'
SINGLE_REPORT_SECTION_URL = REPORT_SECTION_URL + '/{}'


class TestCreateReportEndpoint:
    def generate_json_data(
        self,
        params,
        appliances,
        *,
        param_column_args_mapper=None,
        appliance_section_mapper=None,
        report_kwargs=None,
    ):
        param_ids = [
            param if isinstance(param, str) else param.id for param in params
        ]
        appliance_ids = [
            appliance if isinstance(appliance, str) else appliance.id
            for appliance in appliances
        ]
        param_column_args_mapper = param_column_args_mapper if param_column_args_mapper else {}
        appliance_section_mapper = appliance_section_mapper if appliance_section_mapper else {}
        report_kwargs = report_kwargs if report_kwargs else {}
        columns = []
        sections = []
        for param_id in param_ids:
            columns_kwargs = param_column_args_mapper.get(param_id, {})
            columns.append(
                ReportColumnGenerator.generate_api_data(
                    param_id, **columns_kwargs))

        for appliance_id in appliance_ids:
            section_kwargs = appliance_section_mapper.get(appliance_id, {})
            sections.append(
                ReportSectionGenerator.generate_api_data(
                    appliance_id, columns, **section_kwargs))
        return ReportGenerator.generate_api_data(sections, **report_kwargs)

    def test_engineers_should_be_able_to_create_reports(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        report_name = 'My Golden Report'
        report_section_name = 'Section One Name'
        section_mapper = {appliance.id: {'name': report_section_name}}
        json_data = self.generate_json_data(
            numeric_params, [appliance],
            appliance_section_mapper=section_mapper)
        json_data['name'] = report_name
        url = REPORT_URL.format(org.id)
        add_cookie_to_client(client, user=user_obj)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        report_model = Report.query.filter_by(name=report_name).first()
        response_body = assert_successful_response(response,
                                                   CREATED.format('Report'),
                                                   201)
        data = response_body['data']
        assert data['id'] == report_model.id
        assert data['name'] == report_model.name == report_name

        report_section_query = ReportSection.query.filter_by(
            report_id=report_model.id, appliance_id=appliance.id)
        report_sections = report_section_query.all()
        section_model = report_sections[0]
        assert section_model.name == report_section_name
        assert len(report_sections) == 1
        column_models = ReportColumn.query.filter_by(
            report_section_id=section_model.id).all()
        assert len(column_models) == len(json_data['sections'][0]['columns'])

    def test_regular_users_should_not_be_able_to_create_reports(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='REGULAR USERS', num_of_numeric_units=4)
        add_cookie_to_client(client, user=user_obj)
        json_data = self.generate_json_data(numeric_params, [appliance])
        url = REPORT_URL.format(org.id)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert_user_does_not_have_permission(response)

    def test_report_should_fail_when_a_particular_parameter_id_is_invalid(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, _, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        json_data = self.generate_json_data(['id1', 'id2', 'id3'], [appliance])
        url = REPORT_URL.format(org.id)
        add_cookie_to_client(client, user=user_obj)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        parameter_id_errors = response_body['errors']['parameter_ids']
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert parameter_id_errors['message'] == serialization_error[
            'not_found'].format('Some parameters')
        assert set(parameter_id_errors['invalidValues']) == set(
            ['id1', 'id2', 'id3'])
        assert 'appliance_ids' not in response_body['errors']
        assert response.status_code == 404

    def test_create_report_should_fail_when_a_particular_appliance_id_is_invalid(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        report_section_name = 'Section One Name'
        invalid_appliance_id = 'applianceId'
        section_mapper = {appliance.id: {'name': report_section_name}}
        json_data = self.generate_json_data(
            numeric_params, [invalid_appliance_id],
            appliance_section_mapper=section_mapper)
        url = REPORT_URL.format(org.id)
        add_cookie_to_client(client, user=user_obj)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        appliance_ids_errror = response_body['errors']['appliance_ids']
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert appliance_ids_errror['message'] == serialization_error[
            'not_found'].format('Some appliance you specifed')
        assert appliance_ids_errror['invalidValues'] == [invalid_appliance_id]
        assert 'parameter' not in response_body['errors']
        assert response.status_code == 404

    def test_create_report_should_fail_when_the_start_date_is_more_than_the_end_date(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        report_section_name = 'Section One Name'
        section_mapper = {appliance.id: {'name': report_section_name}}
        report_kwargs = {'start_date': '2019-02-01', 'end_date': '2019-01-01'}
        json_data = self.generate_json_data(
            numeric_params, [appliance],
            report_kwargs=report_kwargs,
            appliance_section_mapper=section_mapper)
        url = REPORT_URL.format(org.id)
        add_cookie_to_client(client, user=user_obj)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_range'].format('Date Range')
        assert response_body['errors']['endDate'] == serialization_error[
            'f1_must_be_gte_f2'].format('end date', 'start date')
        assert response_body['errors']['startDate'] == serialization_error[
            'f1_must_be_lt_f2'].format('start date', 'end date')
        assert 'parameter' not in response_body['errors']
        assert response.status_code == 400


class TestRetrieveReportEndpoint:
    def run_precondition(self,
                         *,
                         appliance,
                         numeric_params,
                         org,
                         user_obj,
                         report_name,
                         param_names=None):
        numeric_params = Parameter.query.filter(
            Parameter.id.in_([param.id for param in numeric_params])).all()
        report = ReportGenerator.generate_model_obj(
            organisation_id=org.id,
            name=report_name,
            created_by_id=user_obj.id,
        )
        report.save()
        report_section = ReportSectionGenerator.generate_model_obj(
            report_id=report.id,
            appliance_id=appliance.id,
            name='Appliance Section')
        report_section.save()
        columns = []
        default_param_names = [
            f'Parameter {index + 1}'
            for index, param in enumerate(numeric_params)
        ]
        param_names = param_names if param_names else default_param_names

        for index, param in enumerate(numeric_params):
            param.name = param_names[index]
            columns.append(
                ReportColumnGenerator.generate_model_obj(
                    report_section_id=report_section.id,
                    parameter_id=param.id,
                    aggregation_type=AggregationType.AVERAGE,
                    aggregate_by_column=True,
                ))
        db.session.commit()
        ReportColumn.bulk_create(columns)
        return report, report_section

    def test_should_retrieve_paginated_report_sections(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        report, report_section = self.run_precondition(
            appliance=appliance,
            numeric_params=numeric_params,
            org=org,
            user_obj=user_obj,
            report_name='Generator I')

        url = REPORT_SECTION_URL.format(org.id, report.id)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response_body['data'][0]['id'] == report_section.id
        assert response_body['data'][0][
            'applianceId'] == report_section.appliance_id
        assert response_body['data'][0]['name'] == report_section.name
        assert response.status_code == 200

    def test_should_retrieve_columns_properly_when_retrieving_report_section(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        param_names = ['Param One', 'Param Two', 'Param Three', 'Param Four']
        report, report_section = self.run_precondition(
            appliance=appliance,
            numeric_params=numeric_params,
            org=org,
            user_obj=user_obj,
            report_name='Generator I',
            param_names=param_names)

        url = SINGLE_REPORT_SECTION_URL.format(org.id, report.id,
                                               report_section.id)
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response_body['data']['id'] == report_section.id
        assert response_body['data']['name'] == report_section.name
        assert response_body['data']['applianceId'] == appliance.id
        assert response_body['data']['columns'][0]['parameter'][
            'name'] in param_names
        assert response_body['data']['columns'][0]['parameter'][
            'valueType'] == 'NUMERIC'
        assert response.status_code == 200

    def test_should_return_404_when_section_id_is_not_found(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        param_names = ['Param One', 'Param Two', 'Param Three', 'Param Four']
        report, report_section = self.run_precondition(
            appliance=appliance,
            numeric_params=numeric_params,
            org=org,
            user_obj=user_obj,
            report_name='Generator I',
            param_names=param_names)

        url = SINGLE_REPORT_SECTION_URL.format(org.id, report.id,
                                               'missing-section-id')
        token = UserGenerator.generate_token(user_obj)
        add_cookie_to_client(client, user_obj, token)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'not_found'].format('Report Section')

        assert response.status_code == 404
