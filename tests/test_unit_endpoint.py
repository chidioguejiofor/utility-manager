import math
import json
from api.models import Unit, Membership, Role, db
from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.success_messages import CREATED, RETRIEVED
from api.utils.constants import COOKIE_TOKEN_KEY
from .mocks.user import UserGenerator
from .mocks.organisation import OrganisationGenerator
from .assertions import assert_paginator_data_values, assert_user_not_in_organisation, add_cookie_to_client

UNITS_ENDPOINT = '/api/org/{}/units'


class TestRetrieveUnit:
    def create_test_precondition(self, unit_objs, init_db,
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
        return unit_json, token, user, org

    def test_should_retrieve_unit_data(self, init_db, client, unit_objs,
                                       saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)
        assert_paginator_data_values(user=user,
                                     created_objs=unit_objs,
                                     client=client,
                                     token=token,
                                     url=UNITS_ENDPOINT.format(org.id),
                                     success_msg=RETRIEVED.format('Unit'))

    def test_should_return_a_404_when_the_user_is_not_part_of_the_organisation(
        self, init_db, client, unit_objs, saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)
        org_two = OrganisationGenerator.generate_model_obj(save=True)

        add_cookie_to_client(client, user, token)
        response = client.get(
            f'{UNITS_ENDPOINT.format(org_two.id)}?name_search=SomeOrg2Unit',
            content_type="application/json")
        assert_user_not_in_organisation(response)

    def test_should_not_retrieve_unit_where_that_are_not_in_specified_organisation(
        self, init_db, client, unit_objs, saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)
        org_two = OrganisationGenerator.generate_model_obj(save=True)
        regular_user_role = Role.query.filter_by(
            name='REGULAR USERS').first().id
        Membership(
            user_id=user.id,
            organisation_id=org_two.id,
            role_id=regular_user_role,
        ).save()

        Unit(
            name='SomeOrg2Unit',
            organisation_id=org_two.id,
            symbol='Some',
        ).save()

        # org
        assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org.id)}?name_search=SomeOrg2Unit',
            success_msg=RETRIEVED.format('Unit'),
            current_page=1,
            total_objects=0,
            max_objects_per_page=10,
            total_pages=0,
            next_page=None,
            prev_page=None,
        )

        # org_two
        assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org_two.id)}?name_search=SomeOrg2Unit',
            success_msg=RETRIEVED.format('Unit'),
            current_page=1,
            total_objects=1,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

    def test_should_paginate_data_correctly_when_paginator_is_provided(
        self, init_db, client, unit_objs, saved_org_and_user_generator):

        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)

        assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org.id)}?page=3&page_limit=4',
            success_msg=RETRIEVED.format('Unit'),
            current_page=3,
            total_objects=len(unit_objs),
            max_objects_per_page=4,
            total_pages=math.ceil(len(unit_objs) / 4),
            next_page=4,
            prev_page=2,
        )

    def test_should_search_for_values_accurately(self, init_db, client,
                                                 unit_objs,
                                                 saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)

        response_body = assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org.id)}?name_search=volTage',
            success_msg=RETRIEVED.format('Unit'),
            current_page=1,
            total_objects=1,
            max_objects_per_page=10,
            total_pages=1,
            next_page=None,
            prev_page=None,
        )

        assert response_body['data'][0]['symbol'] == 'V'
        assert response_body['data'][0]['name'] == 'Voltage'

    def test_should_sort_data_by_name_accurately(self, init_db, client,
                                                 unit_objs,
                                                 saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)

        response_body = assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org.id)}?sort_by=-name',
            success_msg=RETRIEVED.format('Unit'),
            current_page=1,
            total_objects=len(unit_objs),
            max_objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )

        assert response_body['data'][0]['symbol'] == 'yd'
        assert response_body['data'][0]['name'] == 'Yards'

    def test_should_sort_data_by_symbol_accurately(
        self, init_db, client, unit_objs, saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)

        response_body = assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org.id)}?sort_by=-symbol',
            success_msg=RETRIEVED.format('Unit'),
            current_page=1,
            total_objects=len(unit_objs),
            max_objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )

        assert response_body['data'][0]['symbol'] == '\u2126'
        assert response_body['data'][0]['name'] == 'Ohm'

    def test_should_sort_data_by_should_ignore_invalid_query_params(
        self, init_db, client, unit_objs, saved_org_and_user_generator):
        unit_json, token, user, org = self.create_test_precondition(
            unit_objs, init_db, saved_org_and_user_generator)
        response_body = assert_paginator_data_values(
            user=user,
            created_objs=unit_objs,
            client=client,
            token=token,
            url=f'{UNITS_ENDPOINT.format(org.id)}?sort_by=-symbol,fdswcsd',
            success_msg=RETRIEVED.format('Unit'),
            current_page=1,
            total_objects=len(unit_objs),
            max_objects_per_page=10,
            total_pages=math.ceil(len(unit_objs) / 10),
            next_page=2,
            prev_page=None,
        )

        assert response_body['data'][0]['symbol'] == 'Ω'
        assert response_body['data'][0]['name'] == 'Ohm'
