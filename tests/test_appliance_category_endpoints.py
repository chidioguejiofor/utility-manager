from tests.assertions import add_cookie_to_client, assert_paginator_data_values
from api.utils.helper_functions import capitalize_each_word_in_sentence
from api.utils.success_messages import (CREATED, RETRIEVED)
from api.utils.error_messages import serialization_error, authentication_errors
from api.models import ApplianceCategory, db, Appliance, ApplianceParameter
from tests.mocks.user import UserGenerator
from tests.mocks.organisation import OrganisationGenerator
from tests.mocks.appliance_category import ApplianceCategoryGenerator

import json

URL = '/api/org/{}/appliance-category'
RETRIEVE_URL = '/api/org/{}/appliance-category/{}'


def run_test_precondition():
    ApplianceParameter.query.delete()
    ApplianceParameter.query.delete()
    Appliance.query.delete()
    ApplianceCategory.query.delete()
    db.session.commit()


class TestCreateApplianceCategoryEndpoint:
    def test_appliance_category_should_be_created_when_user_is_an_admin_in_the_organisation(
            self, init_db, client):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 201
        response_body = json.loads(response.data)
        assert response_body['message'] == CREATED.format('Appliance Category')
        assert 'data' in response_body
        assert response_body['status'] == 'success'

        model = ApplianceCategory.query.get(response_body['data']['id'])
        assert model.name == capitalize_each_word_in_sentence(
            category_data['name'])
        assert model.description == category_data['description']
        assert model.created_by_id == org.creator.id
        assert model.updated_by_id is None

    def test_should_fail_when_the_appliance_category_already_exists(
            self, client, init_db):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 201
        category_data['name'] = category_data['name'].upper()
        response = client.post(URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 409
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'exists_in_org'].format('Appliance Category')

    def test_should_fail_when_the_body_is_empty(self, client, init_db):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(org.creator)
        add_cookie_to_client(client, org.creator, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps({}),
                               content_type="application/json")
        assert response.status_code == 400
        response_body = json.loads(response.data)
        assert len(response_body['errors']['name']) > 0
        assert len(response_body['errors']['description']) > 0

    def test_should_return_404_when_user_is_not_part_of_org(
            self, init_db, client):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)
        response = client.post(URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        response_body = json.loads(response.data)

        assert response.status_code == 404
        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')
        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_an_admin(
            self, init_db, client, add_user_to_organisation):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        add_user_to_organisation(org, user, role='ENGINEER')

        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)

        response = client.post(URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors['forbidden']
        assert response_body['status'] == 'error'

    def test_should_fail_when_the_user_is_not_verified(
            self, init_db, client, add_user_to_organisation):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        user = UserGenerator.generate_model_obj(save=True, verified=False)
        add_user_to_organisation(org, user, role='ENGINEER')

        category_data = ApplianceCategoryGenerator.generate_api_input_data()
        token = UserGenerator.generate_token(user)
        add_cookie_to_client(client, user, token)

        response = client.post(URL.format(org.id),
                               data=json.dumps(category_data),
                               content_type="application/json")
        assert response.status_code == 403
        response_body = json.loads(response.data)
        assert response_body['message'] == authentication_errors[
            'unverified_user']
        assert response_body['status'] == 'error'


class TestRetrieveApplianceCategory:
    def test_user_should_be_able_to_retrieve_data(
            self, init_db, client, save_appliance_category_to_org):
        run_test_precondition()
        params_objs, org = save_appliance_category_to_org(5)
        token = UserGenerator.generate_token(org.creator)
        url = URL.format(org.id)

        response_body = assert_paginator_data_values(
            user=org.creator,
            created_objs=params_objs,
            client=client,
            token=token,
            url=f'{url}',
            success_msg=RETRIEVED.format('Appliance Category'),
            current_page=1,
            total_objects=5,
            next_page=None,
            prev_page=None,
        )

    def test_should_be_able_to_search_for_specific_appliance_category(
            self, init_db, client, save_appliance_category_to_org):
        run_test_precondition()
        params_objs, org = save_appliance_category_to_org(5)
        token = UserGenerator.generate_token(org.creator)
        url = URL.format(org.id)
        ApplianceCategory(name='My Golden Name',
                          organisation_id=org.id,
                          created_by_id=org.creator.id,
                          description='some_description').save()

        response_body = assert_paginator_data_values(
            user=org.creator,
            created_objs=params_objs,
            client=client,
            token=token,
            url=f'{url}?name_search=lDen Name',
            success_msg=RETRIEVED.format('Appliance Category'),
            current_page=1,
            total_objects=1,
            next_page=None,
            prev_page=None,
        )

        assert len(response_body['data']) == 1
        assert response_body['data'][0]['name'] == 'My Golden Name'


class TestRetrieveSingleApplianceCategory:
    def test_should_retrieve_appliance_category_when_no_parameter_is_associated_with_it(
            self, init_db, client):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(org.creator)

        category = ApplianceCategory(
            name='Generator',
            description='Groups all generators in the appliacation',
            organisation_id=org.id,
            created_by_id=org.creator.id,
        )
        category.save()
        url = RETRIEVE_URL.format(org.id, category.id)
        add_cookie_to_client(client, org.creator, token)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response_body['message'] == RETRIEVED.format(
            'Appliance Category')
        assert response.status_code == 200

        assert response_body['status'] == 'success'
        assert response_body['data']['name'] == category.name
        assert response_body['data']['description'] == category.description
        assert response_body['data']['createdBy']['id'] == org.creator.id
        assert response_body['data']['suggestedParameters'] == []

    def test_should_retrieve_category_with_suggested_parameters(
            self, init_db, client, saved_parameters_to_org):
        run_test_precondition()
        params_objs, org = saved_parameters_to_org(5)
        token = UserGenerator.generate_token(org.creator)

        category = ApplianceCategory(
            name='Generator',
            description='Groups all generators in the appliacation',
            organisation_id=org.id,
            created_by_id=org.creator.id,
        )
        category.save()
        appliance1 = Appliance(
            appliance_category_id=category.id,
            specs={'rating': 500},
            label='id101',
            organisation_id=org.id,
        )
        appliance2 = Appliance(
            appliance_category_id=category.id,
            specs={'rating': 200},
            label='id102a',
            organisation_id=org.id,
        )
        appliance3 = Appliance(
            appliance_category_id=category.id,
            specs={'rating': 200},
            label='id102ab',
            organisation_id=org.id,
        )
        appliance1.save()
        appliance2.save()
        appliance3.save()
        appliance_params = []
        for parameter in params_objs[:2]:
            appliance_params.append(
                ApplianceParameter(parameter_id=parameter.id,
                                   appliance_id=appliance1.id,
                                   organisation_id=org.id), )
        for parameter in params_objs[0:4]:
            appliance_params.append(
                ApplianceParameter(organisation_id=org.id,
                                   parameter_id=parameter.id,
                                   appliance_id=appliance2.id))
        for parameter in params_objs:
            appliance_params.append(
                ApplianceParameter(organisation_id=org.id,
                                   parameter_id=parameter.id,
                                   appliance_id=appliance3.id))
        ApplianceParameter.bulk_create(appliance_params)
        url = RETRIEVE_URL.format(org.id, category.id)
        add_cookie_to_client(client, org.creator, token)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response_body['message'] == RETRIEVED.format(
            'Appliance Category')
        assert response.status_code == 200

        assert response_body['status'] == 'success'
        assert response_body['data']['name'] == category.name
        assert response_body['data']['description'] == category.description
        assert response_body['data']['createdBy']['id'] == org.creator.id
        assert len(response_body['data']['suggestedParameters']) == 5

    def test_should_return_404_when_category_is_not_found(
            self, init_db, client):
        run_test_precondition()
        org = OrganisationGenerator.generate_model_obj(save=True)
        token = UserGenerator.generate_token(org.creator)

        category = ApplianceCategory(
            name='Generator',
            description='Groups all generators in the appliacation',
            organisation_id=org.id,
            created_by_id=org.creator.id,
        )
        category.save()

        url = RETRIEVE_URL.format(org.id, 'unknown-id')
        add_cookie_to_client(client, org.creator, token)
        response = client.get(url)
        response_body = json.loads(response.data)
        assert response_body['message'] == serialization_error[
            'not_found'].format('Appliance Category')
        assert response.status_code == 404

        assert response_body['status'] == 'error'
