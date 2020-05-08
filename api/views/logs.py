import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser, tz
from sqlalchemy.sql import functions
from sqlalchemy import cast, Date, String
from flask import make_response
from api.utils.exceptions import ResponseException
from api.utils.error_messages import serialization_error
from .base import BaseOrgView, BasePaginatedView
from settings import org_endpoint
from flask import request
from api.models import ValueTypeEnum, Log, LogValue, Parameter, db, Unit
from api.schemas import LogSchema
from api.utils.success_messages import SAVED, RETRIEVED


@org_endpoint('/appliances/<string:appliance_id>/export-logs')
class ExportLogsView(BaseOrgView):
    PROTECTED_METHODS = ['GET']

    def parse_seconds_data(self):
        try:
            seconds_offset = int(request.args.get('seconds_offset', 0))
        except ValueError:
            seconds_offset = 0

        if seconds_offset > 12 * 60 * 60 or seconds_offset < -12 * 60 * 60:
            seconds_offset = 0
        try:
            start_date = request.args.get('start_date', str(datetime.utcnow()))
            start_date = parser.parse(start_date)
            end_date = request.args.get('end_date',
                                        str(start_date - timedelta(days=30)))
            end_date = parser.parse(end_date)
            if end_date < start_date:
                raise ResponseException(
                    serialization_error['f1_must_be_gte_f2'].format(
                        'End date', 'Start Date'), 400)

        except ValueError:
            raise ResponseException('Invalid date values', 400)

        return seconds_offset, start_date.date(), end_date.date()

    def get(self, org_id, user_data, appliance_id, membership, **kwargs):
        seconds_offset, start_date, end_date = self.parse_seconds_data()
        date_created_key = 'Date Created'
        coalesce_log_value = functions.coalesce(
            LogValue.text_value, cast(LogValue.numeric_value, String))
        log_data = db.session.query(
            Log.id, Log.created_at, Parameter.name,
            functions.concat(coalesce_log_value, ' ', Unit.symbol)).join(
                LogValue,
                (LogValue.log_id == Log.id) &
                (Log.appliance_id == appliance_id) &
                (cast(Log.created_at, Date) >= start_date) &
                (cast(Log.created_at, Date) <= end_date),
            ).join(Parameter, Parameter.id == LogValue.parameter_id).join(
                Unit,
                Parameter.unit_id == Unit.id,
                isouter=True,
            ).filter(Log.organisation_id == org_id).all()
        if len(log_data) == 0:
            raise ResponseException(
                serialization_error['not_found'].format(
                    'Logs with specified filters'), 404)

        # This pivots the columns and generates the report
        df = pd.DataFrame(
            log_data,
            columns=['log_id', date_created_key, 'parameter', 'value'])
        pivoted_df = df.pivot(index='log_id',
                              columns='parameter',
                              values='value')
        joined_df = pd.merge(df[['log_id', date_created_key]],
                             pivoted_df,
                             on='log_id',
                             how='inner').drop_duplicates()
        joined_df[date_created_key] = joined_df[date_created_key].apply(
            lambda date: date.astimezone(tz.tzoffset(None, seconds_offset)))
        del joined_df['log_id']

        resp = make_response(joined_df.to_csv(index=False))
        resp.headers[
            "Content-Disposition"] = "attachment; filename=exported_log_file.csv"
        resp.headers["Content-Type"] = "text/csv"
        return resp


@org_endpoint('/logs')
class LogsView(BaseOrgView, BasePaginatedView):
    __SCHEMA__ = LogSchema
    __model__ = Log
    PROTECTED_METHODS = ['POST', 'GET']
    ALLOWED_ROLES = {
        'POST': ['OWNER', 'ADMIN', 'ENGINEER'],
        'GET': ['OWNER', 'ADMIN', 'ENGINEER'],
    }

    SORT_KWARGS = {
        'defaults': '-created_at, -updated_at',
        'sort_fields': {'created_at', 'updated_at'}
    }

    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Logs')
    EAGER_LOADING_FIELDS = ['log_values']
    SEARCH_FILTER_ARGS = {
        'appliance_id': {
            'filter_type': 'eq'
        },
    }

    # SCHEMA_EXCLUDE = ['appliance_id']

    def filter_get_method_query(self, query, *args, **kwargs):
        return query.filter_by(organisation_id=kwargs.get('org_id'))

    def post(self, org_id, user_data, membership, **kwargs):
        request_dict = LogSchema().load(request.get_json())
        appliance_id = request_dict['appliance_id']
        log_data = request_dict['log_data']
        param_objs = Parameter.get_parameters_in_appliance(
            org_id, appliance_id).all()

        error_objs = {}

        if len(param_objs) == 0:
            raise ResponseException(
                message=serialization_error['not_found'].format('Appliance'), )
        log_model = Log(organisation_id=org_id,
                        appliance_id=appliance_id,
                        created_by_id=user_data['id'])
        log_model.save(commit=False)
        log_values = []
        for param in param_objs:
            request_value = log_data.get(param.id)
            if request_value is None:
                error_objs[param.id] = serialization_error['required']
            elif (param.value_type == ValueTypeEnum.NUMERIC
                  and self.validate_numeric_value(request_value) is False):
                error_objs[param.id] = serialization_error['number_only']
            elif param.value_type == ValueTypeEnum.NUMERIC:
                log_values.append(
                    LogValue(parameter_id=param.id,
                             log_id=log_model.id,
                             numeric_value=request_value))
            else:
                log_values.append(
                    LogValue(parameter_id=param.id,
                             log_id=log_model.id,
                             text_value=request_value))

        if error_objs:
            raise ResponseException(
                message=serialization_error['invalid_field_data'],
                status_code=400,
                errors=error_objs)

        LogValue.bulk_create(log_values, commit=True)

        saved_log_model = Log.eager('log_values').filter_by(
            id=log_model.id).first()
        return LogSchema().dump_success_data(saved_log_model,
                                             SAVED.format('Log')), 201

    @staticmethod
    def validate_numeric_value(num_with_str):
        try:
            return float(num_with_str)
        except ValueError:
            return False
