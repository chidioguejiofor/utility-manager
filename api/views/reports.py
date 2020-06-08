from settings import org_endpoint, db
from api.utils.error_messages import serialization_error
from flask import request
from .base import BaseOrgView, BaseValidateRelatedOrgModelMixin, BasePaginatedView
from api.utils.success_messages import CREATED, RETRIEVED
from api.schemas import ReportSchema, ReportSectionSchema, ReportColumnSchema
from api.models import Report, ReportSection, ReportColumn, Appliance, Parameter
from api.utils.exceptions import ResponseException


@org_endpoint('/reports')
class ReportsView(BaseOrgView, BasePaginatedView,
                  BaseValidateRelatedOrgModelMixin):
    __model__ = Report
    __SCHEMA__ = ReportSchema
    PROTECTED_METHODS = ['POST', 'GET']
    ALLOWED_ROLES = {
        'POST': ['ENGINEER', 'ADMIN', 'OWNER'],
        'GET': ['ENGINEER', 'ADMIN', 'OWNER'],
    }

    # GET method settings
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': '-created_at,start_date',
        'sort_fields': {'created_at', 'name'}
    }

    EAGER_LOADING_FIELDS = ['created_by', 'updated_by']

    SCHEMA_EXCLUDE = ['sections']
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Reports')

    # Validation Settings
    VALIDATE_RELATED_KWARGS = {
        "parameter_ids": {
            'model':
            Parameter,
            'err_message':
            serialization_error['not_found'].format('Some parameters')
        },
        "appliance_ids": {
            "model":
            Appliance,
            'err_message':
            serialization_error['not_found'].format(
                'Some appliance you specifed')
        },
    }

    def post(self, org_id, user_data, membership):
        report_dict = ReportSchema().load(request.get_json())
        sections = report_dict.pop('sections')
        report_model = Report(**report_dict,
                              organisation_id=org_id,
                              created_by_id=user_data['id'])
        report_model.save(commit=False)
        sections_model_list = []
        column_model_list = []

        appliance_ids = set()
        parameter_ids = set()
        # This is a O(sections * columns_list) but is fast since there's a limit to
        # sections and columns_list length in the schema and it just creates native objects
        # and prepares the bulk create.
        for section in sections:
            columns_list = section.pop('columns')
            appliance_ids.add(section['appliance_id'])
            section_model = ReportSection(**section, report_id=report_model.id)
            section_model.generate_id()
            sections_model_list.append(section_model)
            for report_column_dict in columns_list:
                column_model = ReportColumn(**report_column_dict,
                                            report_section_id=section_model.id)
                parameter_ids.add(report_column_dict['parameter_id'])
                column_model_list.append(column_model)

        self.validate_related_org_models(
            org_id,
            parameter_ids=parameter_ids,
            appliance_ids=appliance_ids,
        )

        ReportSection.bulk_create(sections_model_list, commit=False)
        ReportColumn.bulk_create(column_model_list, commit=True)

        report_dict = ReportSchema().dump_success_data(
            report_model, CREATED.format('Report'))
        return report_dict, 201


@org_endpoint('/reports/<string:report_id>/sections')
class ReportSectionView(BaseOrgView, BasePaginatedView):
    __model__ = ReportSection
    __SCHEMA__ = ReportSectionSchema
    PROTECTED_METHODS = ['GET']
    ALLOWED_ROLES = {
        'GET': ['ENGINEER', 'ADMIN', 'OWNER'],
    }

    # GET method settings
    SEARCH_FILTER_ARGS = {
        'name': {
            'filter_type': 'ilike'
        },
    }
    SCHEMA_EXCLUDE = ['columns']
    SORT_KWARGS = {
        'defaults': '-created_at',
        'sort_fields': {'created_at', 'name'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Report Section')

    def filter_get_method_query(self, query, *args, org_id, report_id,
                                **kwargs):
        return query.filter(ReportSection.report_id == report_id, ).join(
            Report,
            (Report.id == report_id) & (Report.organisation_id == org_id))


@org_endpoint('/reports/<string:report_id>/sections/<string:section_id>')
class ReportColumnView(BaseOrgView):
    PROTECTED_METHODS = ['GET']
    ALLOWED_ROLES = {
        'GET': ['ENGINEER', 'ADMIN', 'OWNER'],
    }

    @staticmethod
    def get(report_id, org_id, section_id, **kwargs):
        section = ReportSection.eager(
            'columns', 'columns.parameter', 'columns.parameter.unit').filter(
                ReportSection.id == section_id).join(
                    Report, (Report.id == report_id) &
                    (Report.organisation_id == org_id)).first()
        if not section:
            raise ResponseException(
                serialization_error['not_found'].format('Report Section'), 404)
        schema = ReportSectionSchema()

        return schema.dump_success_data(section,
                                        RETRIEVED.format('Report Section'))
