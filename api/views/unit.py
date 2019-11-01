from .base import BaseView, FilterByQueryMixin
from settings import endpoint
from flask import request
from api.models import Unit, Membership, RoleEnum
from api.schemas import UnitSchema
from api.utils.exceptions import MessageOnlyResponseException
from api.utils.success_messages import CREATED, RETRIEVED
from api.utils.error_messages import serialization_error


# /org/<string:org_id>/parameters
@endpoint('/org/<string:org_id>/units')
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

    def get(self, org_id):
        self.decode_token(check_user_is_verified=True)
        query_params = request.args
        query = self.search_model(query_params, org_id=org_id)
        page_query, meta = self.paginate_query(query, query_params)
        data = UnitSchema(many=True).dump_success_data(
            page_query, message=RETRIEVED.format('Unit'))
        data['meta'] = meta
        return data, 200

    def post(self, org_id):
        user_data = self.decode_token(check_user_is_verified=True)
        input_data = request.get_json()
        input_data['organisationId'] = org_id
        unit = UnitSchema().load(input_data)
        membership = Membership.query.filter_by(
            user_id=user_data['id'],
            organisation_id=org_id,
        ).first()
        if not membership:
            raise MessageOnlyResponseException(
                status_code=404,
                message=serialization_error['not_found'].format(
                    'Organisation'))

        if membership.role not in [RoleEnum.OWNER, RoleEnum.ENGINEER]:
            raise MessageOnlyResponseException(
                status_code=403, message=serialization_error['not_an_admin'])

        unit_already_exists = Unit.query.filter_by(
            name=unit.name,
            greek_symbol_num=unit.greek_symbol_num,
            letter_symbol=unit.letter_symbol,
            organisation_id=None,
        ).count()
        if unit_already_exists:
            raise MessageOnlyResponseException(
                status_code=400, message=Unit.__unique_violation_msg__)

        unit.save()
        unit_data = UnitSchema().dump_success_data(unit,
                                                   CREATED.format('Unit'))

        return unit_data, 201
