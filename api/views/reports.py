from sqlalchemy import func
from settings import org_endpoint, db
from api.utils.error_messages import serialization_error
from api.utils.exceptions import ResponseException
from flask import request
from .base import BaseOrgView
from api.utils.success_messages import CREATED
from api.schemas import ReportSchema
from api.models import Report, ReportSection, ReportColumn, Appliance, Organisation, Parameter


@org_endpoint('/reports')
class ReportsView(BaseOrgView):
    PROTECTED_METHODS = ['POST']
    ALLOWED_ROLES = {'POST': ['ENGINEER', 'ADMIN', 'OWNER']}

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
        self.validate_param_and_appliance_ids(org_id, parameter_ids,
                                              appliance_ids)

        ReportSection.bulk_create(sections_model_list, commit=False)
        ReportColumn.bulk_create(column_model_list, commit=True)

        report_dict = ReportSchema().dump_success_data(
            report_model, CREATED.format('Report'))
        return report_dict, 201

    @staticmethod
    def validate_param_and_appliance_ids(org_id, parameter_ids, appliance_ids):
        string_agg = func.string_agg
        org_filter = Organisation.id == org_id
        param_filter = ((Parameter.organisation_id == Organisation.id) &
                        (Parameter.id.in_(parameter_ids)) & org_filter)
        appliance_filter = (org_filter &
                            (Appliance.organisation_id == Organisation.id) &
                            (Appliance.id.in_(appliance_ids)))
        validation_info = db.session.query(
            Organisation.id, string_agg(Appliance.id.distinct(), ','),
            string_agg(Parameter.id.distinct(),
                       ',')).join(Parameter, param_filter, isouter=True).join(
                           Appliance, appliance_filter,
                           isouter=True).filter(org_filter).group_by(
                               Organisation.id).all()
        _, found_appliances, found_parameters = validation_info[0]
        errors = {}
        if not found_appliances or len(
                found_appliances.split(',')) != len(appliance_ids):
            errors['appliance_ids'] = serialization_error['not_found'].format(
                'Some appliance you specifed')
        if not found_parameters or len(
                found_parameters.split(',')) != len(parameter_ids):
            errors['parameter'] = serialization_error['not_found'].format(
                'Some parameters')
        if errors:
            raise ResponseException(serialization_error['invalid_field_data'],
                                    404,
                                    errors=errors)
