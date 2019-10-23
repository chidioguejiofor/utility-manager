from .base import BaseView, FilterByQueryMixin
from settings import endpoint
from flask import request
from api.models import Unit, Membership
from api.schemas import UnitSchema
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.success_messages import CREATED, RETRIEVED
from api.utils.error_messages import serialization_error


@endpoint('/units')
class UnitView(BaseView, FilterByQueryMixin):
    __model__ = Unit

    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
        'letter_symbol': {
            'filter_type': 'ilike'
        },
        'greek_symbol': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': 'name,letter_symbol',
        'sort_fields': {'name', 'letter_symbol'}
    }

    def get(self):
        self.decode_token(check_user_is_verified=True)
        query_params = request.args
        query = self.search_model(query_params)
        page_query, meta = self.paginate_query(query, query_params)
        data = UnitSchema(many=True).dump_success_data(
            page_query, message=RETRIEVED.format('Unit'))
        data['meta'] = meta
        return data, 200

    def post(self):
        user_data = self.decode_token(check_user_is_verified=True)
        unit = UnitSchema().load(request.get_json())
        valid_memberships = Membership.query.filter_by(
            user_id=user_data['id']).filter(
                Membership.role.in_(['OWNER', 'ENGINEER'])).count()
        if valid_memberships == 0:
            raise MessageOnlyResponseException(
                status_code=403, message=serialization_error['not_an_admin'])

        unit.save()
        unit_data = UnitSchema().dump_success_data(unit,
                                                   CREATED.format('Unit'))

        return unit_data, 201
