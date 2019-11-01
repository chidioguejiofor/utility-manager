import math
import json
from api.models import Unit, Membership
from api.utils.error_messages import serialization_error
from api.utils.success_messages import CREATED, RETRIEVED
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from .assertions import assert_paginator_meta

UNITS_ENDPOINT = '/api/org/{}/units'


class TestCreateUnitEndpoint:
    def test_should_create_unit_successfully_when_user_is_valid(
            self, app, init_db, client, saved_org_and_user_generator):
        user, org = saved_org_and_user_generator
        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT.format(org.id),
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 201
        assert response_body['data']['name'] == unit_json['name']
        assert response_body['data']['letterSymbol'] == unit_json[
            'letterSymbol']
        assert response_body['data']['createdAt'] is not None
        assert response_body['message'] == CREATED.format('Unit')

    def test_unit_should_not_be_created_when_you_it_has_already_been_seeded(
            self, app, init_db, client, saved_org_and_user_generator):
        user, org = saved_org_and_user_generator
        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }

        Unit(
            name='Joules',
            letter_symbol='J',
            organisation_id=None,
        ).save()

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT.format(org.id),
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert 'data' not in response_body

        assert response_body['message'] == \
               serialization_error['exists_in_org'].format('Unit')

    def test_the_endpoint_when_user_is_not_a_member_of_current_organisation_returns_404(
            self, app, init_db, client, saved_org_and_user_generator):
        user, org = saved_org_and_user_generator
        user_two = UserGenerator.generate_model_obj(save=True, verified=True)
        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user_two)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT.format(org.id),
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 404
        assert 'data' not in response_body
        assert response_body['message'] == serialization_error[
            'not_found'].format('Organisation')

    def test_unit_should_not_be_created_if_the_user_is_not_an_admin_in_this_organisation(
            self, app, init_db, client, saved_org_and_user_generator):
        user, org = saved_org_and_user_generator
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        Membership(user_id=user.id, organisation_id=org.id).save()
        unit_json = {
            'name': 'Joules2',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT.format(org.id),
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 403
        assert response_body['message'] == serialization_error['not_an_admin']

    def test_should_fail_when_data_is_missing(self, app, init_db, client,
                                              saved_org_and_user_generator):
        user, org = saved_org_and_user_generator

        unit_json = {}
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT.format(org.id),
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['name'][
            0] == 'Missing data for required field.'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']


class TestRetrieveUnit:
    def test_should_retrieve_unit_data(self, init_db, client, unit_objs,
                                       saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()
        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(UNITS_ENDPOINT.format(org.id),
                              data=json.dumps(unit_json),
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(unit_objs),
            objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )

    def test_should_not_retrieve_unit_where_that_are_not_in_specified_organisation(
            self, init_db, client, unit_objs, saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()
        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator
        org_two = OrganisationGenerator.generate_model_obj(save=True)
        Unit(
            name='SomeOrg2Unit',
            organisation_id=org_two.id,
            letter_symbol='Some',
        ).save()
        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{UNITS_ENDPOINT.format(org.id)}?name_search=SomeOrg2Unit',
            data=json.dumps(unit_json),
            content_type="application/json")
        response_two = client.get(
            f'{UNITS_ENDPOINT.format(org_two.id)}?name_search=SomeOrg2Unit',
            data=json.dumps(unit_json),
            content_type="application/json")
        response_body_two = json.loads(response_two.data)

        response_body = json.loads(response.data)
        # Checking res_one data
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=0,
            objects_per_page=10,
            total_pages=0,
            next_page=None,
            prev_page=None,
        )
        # Checking res_two data
        assert response.status_code == 200
        assert response_body_two['message'] == RETRIEVED.format('Unit')
        assert response_body_two['status'] == 'success'
        assert response_body_two['data'][0]['name'] == 'SomeOrg2Unit'
        assert_paginator_meta(
            response_body_two,
            current_page=1,
            total_objects=1,
            objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

    def test_should_paginate_data_correctly_when_paginator_is_provided(
            self, init_db, client, unit_objs, saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{UNITS_ENDPOINT.format(org.id)}?page=3&page_limit=4',
            data=json.dumps(unit_json),
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert_paginator_meta(
            response_body,
            current_page=3,
            total_objects=len(unit_objs),
            objects_per_page=4,
            total_pages=math.ceil(len(unit_objs) / 4),
            next_page=4,
            prev_page=2,
        )

    def test_should_search_for_values_accurately(self, init_db, client,
                                                 unit_objs,
                                                 saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{UNITS_ENDPOINT.format(org.id)}?name_search=volTage',
            data=json.dumps(unit_json),
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert response_body['data'][0]['letterSymbol'] == 'V'
        assert response_body['data'][0]['name'] == 'Voltage'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=1,
            objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

    def test_should_sort_data_by_name_accurately(self, init_db, client,
                                                 unit_objs,
                                                 saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(f'{UNITS_ENDPOINT.format(org.id)}?sort_by=-name',
                              content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert response_body['data'][0]['letterSymbol'] == 'yd'
        assert response_body['data'][0]['name'] == 'Yards'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(unit_objs),
            objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )

    def test_should_sort_data_by_symbol_accurately(
            self, init_db, client, unit_objs, saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{UNITS_ENDPOINT.format(org.id)}?sort_by=-letter_symbol',
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert response_body['data'][0]['letterSymbol'] == 'yd'
        assert response_body['data'][0]['name'] == 'Yards'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(unit_objs),
            objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )

    def test_should_sort_data_by_should_ignore_invalid_query_params(
            self, init_db, client, unit_objs, saved_org_and_user_generator):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user, org = saved_org_and_user_generator

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{UNITS_ENDPOINT.format(org.id)}?sort_by=some-invalid-field,-name,didsucndaew',
            content_type="application/json")
        response_body = json.loads(response.data)
        assert response.status_code == 200
        assert response_body['message'] == RETRIEVED.format('Unit')
        assert response_body['status'] == 'success'
        assert response_body['data'][0]['letterSymbol'] == 'yd'
        assert response_body['data'][0]['name'] == 'Yards'
        assert_paginator_meta(
            response_body,
            current_page=1,
            total_objects=len(unit_objs),
            objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )
