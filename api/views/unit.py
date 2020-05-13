from .base import BaseView, BasePaginatedView, BaseOrgView
from settings import endpoint
from flask import request
from api.models import Unit
from api.schemas import UnitSchema
from api.utils.exceptions import ResponseException
from api.utils.success_messages import CREATED, RETRIEVED


@endpoint('/org/<string:org_id>/units')
class UnitView(BaseOrgView, BasePaginatedView):
    __model__ = Unit
    __SCHEMA__ = UnitSchema
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Unit')

    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
        'symbol': {
            'filter_type': 'ilike'
        },
    }
    SCHEMA_EXCLUDE = ['organisation_id']
    SORT_KWARGS = {
        'defaults': 'name,symbol',
        'sort_fields': {'name', 'symbol'}
    }
    PROTECTED_METHODS = ['GET', 'POST']

    ALLOWED_ROLES = {'POST': ['OWNER', 'ENGINEER', 'ADMIN']}
