from api.models.reports import ReportSection, Report, ReportColumn, AggregationType
from .base import BaseGenerator


class ReportGenerator(BaseGenerator):
    __model__ = Report

    @staticmethod
    def generate_model_obj_dict(*args, **kwargs):
        return {
            "name": kwargs.get('name', "Report for 2020 for Generator 1"),
            "start_date": kwargs.get('start_date', "2019-01-01"),
            "end_date": kwargs.get('end_date', "2019-02-01"),
            "organisation_id": kwargs['organisation_id'],
            "created_by_id": kwargs['created_by_id'],
        }

    @staticmethod
    def generate_api_data(sections, **kwargs):
        return {
            "name": kwargs.get('name', "Report for 2020 for Generator 1"),
            "startDate": kwargs.get('start_date', "2019-01-01"),
            "endDate": kwargs.get('end_date', "2019-02-01"),
            "sections": sections
        }


class ReportSectionGenerator(BaseGenerator):
    __model__ = ReportSection

    @staticmethod
    def generate_model_obj_dict(*, appliance_id, report_id, name):
        return {
            "report_id": report_id,
            "appliance_id": appliance_id,
            "name": name,
        }

    @staticmethod
    def generate_api_data(appliance_id, columns, **kwargs):
        return {
            "applianceId": appliance_id,
            "name": kwargs.get('name', "Stats for Energy Consumed"),
            "columns": columns
        }


class ReportColumnGenerator(BaseGenerator):
    __model__ = ReportColumn

    @staticmethod
    def generate_model_obj_dict(*, parameter_id, **kwargs):
        return {
            "parameter_id":
            parameter_id,
            'report_section_id':
            kwargs['report_section_id'],
            "aggregation_type":
            kwargs.get('aggregation_type', AggregationType.AVERAGE),
            "aggregate_by_column":
            kwargs.get('aggregate_by_column', False),
        }

    @staticmethod
    def generate_api_data(parameter_id, **kwargs):
        return {
            "parameterId": parameter_id,
            "aggregationType": kwargs.get('aggregation_type', "AVERAGE"),
            "aggregateByColumn": kwargs.get('aggregate_by_column', False),
        }
