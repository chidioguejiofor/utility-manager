import json
from api.models import Report, ReportSection, ReportColumn

from api.utils.error_messages import serialization_error, parameter_errors, authentication_errors
from api.utils.success_messages import CREATED, RETRIEVED
from .mocks.user import UserGenerator
from .assertions import add_cookie_to_client, assert_user_does_not_have_permission, assert_successful_response

REPORT_URL = '/api/org/{}/reports'


class ReportGenerator:
    @staticmethod
    def generate_api_data(sections, **kwargs):
        return {
            "name": kwargs.get('name', "Report for 2020 for Generator 1"),
            "startDate": kwargs.get('start_date', "2019-01-01"),
            "endDate": kwargs.get('end_date', "2019-02-01"),
            "sections": sections
        }


class ReportSectionGenerator:
    @staticmethod
    def generate_api_data(appliance_id, columns, **kwargs):
        return {
            "applianceId": appliance_id,
            "name": kwargs.get('name', "Stats for Energy Consumed"),
            "columns": columns
        }


class ReportColumnGenerator:
    @staticmethod
    def generate_api_data(parameter_id, **kwargs):
        return {
            "parameterId": parameter_id,
            "aggregationType": kwargs.get('aggregation_type', "AVERAGE"),
            "aggregateByColumn": kwargs.get('aggregate_by_column', False),
        }


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
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['parameter'] == serialization_error[
            'not_found'].format('Some parameters')
        assert 'appliance_ids' not in response_body['errors']
        assert response.status_code == 404

    def test_create_report_should_fail_when_a_particular_appliance_id_is_invalid(
            self, init_db, client, saved_appliance_generator):
        org, user_obj, numeric_params, _, appliance = saved_appliance_generator(
            user_role='ENGINEER', num_of_numeric_units=4)
        report_section_name = 'Section One Name'
        section_mapper = {appliance.id: {'name': report_section_name}}
        json_data = self.generate_json_data(
            numeric_params, ['applianceId'],
            appliance_section_mapper=section_mapper)
        url = REPORT_URL.format(org.id)
        add_cookie_to_client(client, user=user_obj)
        response = client.post(url,
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['appliance_ids'] == serialization_error[
            'not_found'].format('Some appliance you specifed')
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
            'f1_must_be_gt_f2'].format('end date', 'start date')
        assert response_body['errors']['startDate'] == serialization_error[
            'f1_must_be_lt_f2'].format('start date', 'end date')
        assert 'parameter' not in response_body['errors']
        assert response.status_code == 400
