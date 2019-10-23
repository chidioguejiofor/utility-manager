import math
import json
from api.models import Unit
from api.utils.error_messages import serialization_error
from api.utils.success_messages import CREATED, RETRIEVED
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from .assertions import assert_paginator_meta

UNITS_ENDPOINT = '/api/units'


class TestCreateUnitEndpoint:
    def test_should_create_unit_successfully_when_user_is_valid(
            self, app, init_db, client):
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        OrganisationGenerator.generate_model_obj(creator_id=user.id, save=True)

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT,
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 201
        assert response_body['data']['name'] == unit_json['name']
        assert response_body['data']['letterSymbol'] == unit_json[
            'letterSymbol']
        assert response_body['data']['createdAt'] is not None
        assert response_body['message'] == CREATED.format('Unit')

    def test_should_not_create_if_the_user_is_not_an_admin_in_any_organisation(
            self, app, init_db, client):
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        unit_json = {
            'name': 'Joules2',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT,
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 403
        assert response_body['message'] == serialization_error['not_an_admin']

    def test_should_fail_when_data_is_missing(self, app, init_db, client):
        user = UserGenerator.generate_model_obj(save=True, verified=True)
        OrganisationGenerator.generate_model_obj(creator_id=user.id, save=True)

        unit_json = {}
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.post(UNITS_ENDPOINT,
                               data=json.dumps(unit_json),
                               content_type="application/json")

        response_body = json.loads(response.data)
        assert response.status_code == 400
        assert response_body['errors']['name'][
            0] == 'Missing data for required field.'
        assert response_body['message'] == serialization_error[
            'invalid_field_data']


class TestRetrieveUnit:
    def test_should_retrieve_unit_data(self, init_db, client, unit_objs):
        Unit.query.delete()
        init_db.session.commit()
        Unit.bulk_create(unit_objs)
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(UNITS_ENDPOINT,
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

    def test_should_paginate_data_correctly_when_paginator_is_provided(
            self, init_db, client, unit_objs):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(f'{UNITS_ENDPOINT}?page=3&page_limit=4',
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
                                                 unit_objs):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        unit_json = {
            'name': 'Joules',
            'letterSymbol': 'J',
        }
        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(f'{UNITS_ENDPOINT}?name_search=volTage',
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
                                                 unit_objs):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(f'{UNITS_ENDPOINT}?sort_by=-name',
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

    def test_should_sort_data_by_symbol_accurately(self, init_db, client,
                                                   unit_objs):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(f'{UNITS_ENDPOINT}?sort_by=-letter_symbol',
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
            self, init_db, client, unit_objs):
        Unit.query.delete()
        init_db.session.commit()

        Unit.bulk_create(unit_objs)
        user = UserGenerator.generate_model_obj(save=True, verified=True)

        token = UserGenerator.generate_token(user)

        client.set_cookie('/', 'token', token)
        response = client.get(
            f'{UNITS_ENDPOINT}?sort_by=some-invalid-field,-name,didsucndaew',
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
