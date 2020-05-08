from marshmallow import fields, post_load
from api.utils.exceptions import ResponseException
from api.models import AggregationType
from marshmallow_enum import EnumField
from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, ListField, IDField)
from api.utils.error_messages import serialization_error


class ReportColumn(BaseSchema):
    parameter_id = IDField(required=True, data_key='parameterId')
    aggregation_type = EnumField(enum=AggregationType,
                                 data_key='aggregationType',
                                 by_value=False,
                                 required=True)
    aggregate_by_column = fields.Boolean(required=True,
                                         data_key='aggregateByColumn')


class ReportSection(BaseSchema):
    name = StringField(required=True)
    columns = ListField(fields.Nested(ReportColumn),
                        min_length=1,
                        max_length=50,
                        required=True)
    appliance_id = StringField(data_key='applianceId')


class Report(BaseSchema, AbstractSchemaWithTimeStampsMixin,
             AbstractUserActionMixin):
    name = StringField(capitalize=True, required=True)
    start_date = fields.Date(required=True, data_key='startDate')
    end_date = fields.Date(required=True, data_key='endDate')
    sections = ListField(fields.Nested(ReportSection),
                         min_length=1,
                         max_length=5,
                         required=True)

    @post_load
    def make_user(self, data, **kwargs):
        if data['start_date'] > data['end_date']:
            # Date Range
            raise ResponseException(
                serialization_error['invalid_range'].format('Date Range'),
                errors={
                    'endDate':
                    serialization_error['f1_must_be_gte_f2'].format(
                        'end date', 'start date'),
                    'startDate':
                    serialization_error['f1_must_be_lt_f2'].format(
                        'start date', 'end date'),
                })
        return data
