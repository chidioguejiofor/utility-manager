from .base import BaseView, BasePaginatedView
from settings import endpoint
from flask import request
from api.models import Unit, Membership
from api.schemas import UnitSchema
from api.utils.exceptions import ResponseException
from api.utils.success_messages import CREATED, RETRIEVED
from api.services.redis_util import RedisUtil
from api.utils.error_messages import serialization_error


# /org/<string:org_id>/parameters
@endpoint('/org/<string:org_id>/units')
class UnitView(BaseView, BasePaginatedView):
    __model__ = Unit
    __SCHEMA__ = UnitSchema
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Unit')

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
    protected_methods = ['GET', 'POST']

    def filter_get_method_query(self, query, **kwargs):
        org_id = kwargs['org_id']
        return query.filter((self.__model__.organisation_id == org_id)
                            | (self.__model__.organisation_id.is_(None)))

    def post(self, org_id, user_data):
        input_data = request.get_json()
        input_data['organisationId'] = org_id
        unit = UnitSchema().load(input_data)
        membership = Membership.query.filter_by(
            user_id=user_data['id'],
            organisation_id=org_id,
        ).first()
        if not membership:
            raise ResponseException(
                status_code=404,
                message=serialization_error['not_found'].format(
                    'Organisation'))

        allowed_rows = [
            RedisUtil.get_role_id('OWNER'),
            RedisUtil.get_role_id('ENGINEER'),
            RedisUtil.get_role_id('ADMIN'),
        ]
        if membership.role.id not in allowed_rows:
            raise ResponseException(
                status_code=403, message=serialization_error['not_an_admin'])

        unit_already_exists = Unit.query.filter_by(
            name=unit.name,
            greek_symbol_num=unit.greek_symbol_num,
            letter_symbol=unit.letter_symbol,
            organisation_id=None,
        ).count()
        if unit_already_exists:
            raise ResponseException(status_code=400,
                                    message=Unit.__unique_violation_msg__)

        unit.save()
        unit_data = UnitSchema().dump_success_data(unit,
                                                   CREATED.format('Unit'))

        return unit_data, 201
