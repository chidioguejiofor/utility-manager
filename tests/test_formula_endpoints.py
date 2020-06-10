from tests.assertions import (add_cookie_to_client, assert_successful_response,
                              assert_paginator_data_values,
                              assert_user_not_in_organisation,
                              assert_unverified_user)
from api.utils.success_messages import (CREATED, RETRIEVED)
from api.utils.error_messages import formula_errors, serialization_error, model_operations
from api.models import Formula, db, Appliance, ApplianceParameter, Parameter
from tests.mocks.user import UserGenerator
from tests.mocks.organisation import OrganisationGenerator
from tests.mocks.paramter import ParameterGenerator
from tests.mocks.formula import (failure_edge_cases,
                                 generate_formula_with_parameter_id_data,
                                 generate_formula_with_formula_id_data)

import json

URL = '/api/org/{}/formulas'


class TestCreateFormulaEndpoint:
    def test_should_create_formula_when_valid_data_is_passed(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        parameter = ParameterGenerator.generate_model_obj(
            organisation_id=org.id, save=True)
        json_data = generate_formula_with_parameter_id_data(
            parameter_id=parameter.id)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = assert_successful_response(response,
                                                   CREATED.format('Formula'),
                                                   201)
        formula_id = response_body['data']['id']
        formula = Formula.query.filter(Formula.id == formula_id).first()
        assert response_body['data']['name'] == json_data['name']
        assert formula.has_formula is False

    def test_should_create_formula_with_other_formulas(self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        parameter = ParameterGenerator.generate_model_obj(
            organisation_id=org.id, save=True)
        json_data = generate_formula_with_parameter_id_data(
            parameter_id=parameter.id)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        #  Creates the first formula
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = assert_successful_response(response,
                                                   CREATED.format('Formula'),
                                                   201)
        formula_id = response_body['data']['id']

        #  Uses the first formula to create the second
        json_data = generate_formula_with_formula_id_data(
            formula_id=formula_id)
        json_data['name'] = 'Formula One'
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        response_body = assert_successful_response(response,
                                                   CREATED.format('Formula'),
                                                   201)
        formula_id = response_body['data']['id']
        formula = Formula.query.filter(Formula.id == formula_id).first()
        assert response_body['data']['name'] == json_data['name']
        assert formula.has_formula is True

    def test_should_raise_error_when_a_unit_id_is_not_found(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        invalid_unit_id = 'invalid_unit'
        parameter = ParameterGenerator.generate_model_obj(
            organisation_id=org.id, save=True)
        json_data = generate_formula_with_parameter_id_data(
            parameter_id=parameter.id)
        json_data['unitId'] = invalid_unit_id
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 404
        response_body = json.loads(response.data)
        unit_id_error = response_body['errors']['unitId']
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert unit_id_error['invalidValues'] == [invalid_unit_id]
        assert unit_id_error['message'] == serialization_error[
            'not_found'].format('Unit')

    def test_should_raise_error_when_a_parameter_id_is_not_found(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        invalid_parameter = 'invalid-parameter-id'
        json_data = generate_formula_with_parameter_id_data(
            parameter_id=invalid_parameter)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 404
        response_body = json.loads(response.data)
        parameter_id_error = response_body['errors']['parameterId']
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert parameter_id_error['invalidValues'] == [invalid_parameter]
        assert parameter_id_error['message'] == serialization_error[
            'not_found'].format('Some parameter(s) you specified')

    def test_should_raise_error_when_a_formula_id_is_not_found(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        invalid_formula = 'invalid-formula-id'
        json_data = generate_formula_with_parameter_id_data(
            parameter_id=invalid_formula)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 404
        response_body = json.loads(response.data)
        parameter_id_error = response_body['errors']['formulaId']
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert parameter_id_error['invalidValues'] == [invalid_formula]
        assert parameter_id_error['message'] == serialization_error[
            'not_found'].format('Some parameter(s) you specified')

    def test_should_raise_error_when_a_formula_id_is_not_found(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        invalid_formula = 'invalid-formula-id'
        json_data = generate_formula_with_parameter_id_data(
            parameter_id=invalid_formula)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 404
        response_body = json.loads(response.data)
        parameter_id_error = response_body['errors']['parameterId']
        assert response_body['message'] == serialization_error[
            'not_found_fields']
        assert parameter_id_error['invalidValues'] == [invalid_formula]
        assert parameter_id_error['message'] == serialization_error[
            'not_found'].format('Some parameter(s) you specified')

    def test_should_return_400_when_some_brackets_are_not_closed(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['(a+b(']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == formula_errors[
            'missing_closing_bracket']

    def test_should_return_400_when_a_closing_bracket_immediately_follows_an_opening_one(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['a+()b']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == formula_errors[
            'awkward_value'].format(3)

    def test_should_fail_when_when_the_formula_has_invalid_brackets(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['((a+)+)']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == formula_errors[
            'awkward_value'].format(4)

    def test_should_fail_when_when_the_formula_is_missing_a_variable(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['((a+b)+)']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == formula_errors[
            'awkward_value'].format(7)

    def test_should_fail_when_formula_starts_with_a_closing_bracket(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases[')a+b)']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == formula_errors[
            'awkward_value'].format(0)

    def test_should_fail_when_formula_ends_with_a_math_operation(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['(a+b)+']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == formula_errors[
            'math_operation_at_end']

    def test_should_fail_when_there_is_a_parameter_field_that_is_missing_a_parameter_id_key(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['missing_parameter_id']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        print(response_body['errors'])
        assert response_body['errors']['tokens']['1']['parameter_id'][0] == (
            formula_errors['required_field_for_type'].format('PARAMETER'))

    def test_should_fail_when_there_is_a_formula_that_is_missing_a_formula_id_id_key(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['missing_formula_id']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        print(response_body['errors'])
        assert response_body['errors']['tokens']['1']['formula_id'][0] == (
            formula_errors['required_field_for_type'].format('FORMULA'))

    def test_should_fail_when_there_is_a_symbol_that_is_missing_a_symbol_key(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['symbol_with_missing_symbol_key']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['tokens']['2']['symbol'][0] == (
            formula_errors['required_field_for_type'].format('SYMBOL'))

    def test_should_fail_when_there_is_a_constant_that_is_missing_a_constant_key(
            self, init_db, client):
        org = OrganisationGenerator.generate_model_obj(save=True)
        json_data = failure_edge_cases['missing_constant']
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(json_data),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'invalid_field_data']
        assert response_body['errors']['tokens']['1']['constant'][0] == (
            formula_errors['required_field_for_type'].format('CONSTANT'))
