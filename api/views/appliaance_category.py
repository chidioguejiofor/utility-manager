import numpy as np
from sqlalchemy.orm import joinedload
from .base import BaseOrgView, BasePaginatedView
from api.utils.exceptions import ResponseException
from api.models import ApplianceCategory, ApplianceParameter, Appliance, Parameter, db
from settings import org_endpoint
from flask import request
from api.schemas import ApplianceCategorySchema, ParameterSchema
from api.utils.success_messages import CREATED, RETRIEVED
from api.utils.error_messages import serialization_error


@org_endpoint('/appliance-category/<string:category_id>')
class SuggestParameter(BaseOrgView):
    PROTECTED_METHODS = ['GET']

    def get(self, org_id, user_data, membership, category_id):
        category_filter_ = [
            ApplianceCategory.organisation_id == org_id,
            (Appliance.organisation_id == org_id) |
            (Appliance.organisation_id == None),
            (Parameter.organisation_id == org_id) |
            (Parameter.organisation_id == None),
            ApplianceCategory.id == category_id,
        ]
        where_clause_filter = np.bitwise_and.reduce(category_filter_)

        model_objs = db.session.query(ApplianceCategory, Parameter).join(
            Appliance,
            ApplianceCategory.id == Appliance.appliance_category_id,
            isouter=True).join(
                ApplianceParameter,
                ApplianceParameter.appliance_id == Appliance.id,
                isouter=True).join(
                    Parameter,
                    Parameter.id == ApplianceParameter.parameter_id,
                    isouter=True).options(
                        joinedload(Parameter.unit),
                        joinedload(ApplianceCategory.created_by)).filter(
                            where_clause_filter).all()

        if len(model_objs) == 0:
            raise ResponseException(
                status_code=404,
                message=serialization_error['not_found'].format(
                    'Appliance Category'))
        exclude_param_fields = [
            'created_at', 'updated_at', 'validation', 'editable', 'created_by',
            'updated_by', 'organisation_id'
        ]
        cat_exclude = ['updated_by']
        array = np.array(model_objs).T
        suggested_params = array[1]
        filter_data = (param for param in suggested_params
                       if param is not None)
        suggested_params = [p for p in filter_data]
        dumped_params = ParameterSchema(exclude=exclude_param_fields,
                                        many=True).dump(suggested_params)

        res_data = ApplianceCategorySchema(
            exclude=cat_exclude).dump_success_data(
                array[0][0], RETRIEVED.format('Appliance Category'))

        res_data['data']['suggestedParameters'] = dumped_params

        return res_data


@org_endpoint('/appliance-category')
class ApplianceCategoryView(BaseOrgView, BasePaginatedView):
    __SCHEMA__ = ApplianceCategorySchema
    __model__ = ApplianceCategory
    PROTECTED_METHODS = ['POST', 'GET']

    ALLOWED_ROLES = {'POST': ['MANAGER', 'OWNER', 'ADMIN']}

    # query settings
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': 'created_at',
        'sort_fields': {'created_at', 'name'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Appliance Category')
    SCHEMA_EXCLUDE = ['organisation_id']

    def post(self, org_id, user_data, membership):
        json_data = request.get_json()
        json_data = json_data if json_data else {}
        json_data['organisation_id'] = org_id
        json_data['created_by_id'] = user_data['id']
        category_obj = ApplianceCategorySchema().load(json_data)
        category_obj.save()
        res_data = ApplianceCategorySchema().dump_success_data(
            category_obj, CREATED.format('Appliance Category'))
        return res_data, 201
