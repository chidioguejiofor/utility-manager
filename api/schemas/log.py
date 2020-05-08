from marshmallow import fields
from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, ListField, IDField)


class Log(BaseSchema, AbstractSchemaWithTimeStampsMixin,
          AbstractUserActionMixin):
    appliance_id = StringField(required=True, data_key='applianceId')
    log_data = fields.Dict(required=True, load_only=True, data_key='logData')
    log_values = fields.Method('retrieve_log_value',
                               data_key='logValues',
                               dump_only=True)

    def retrieve_log_value(self, obj, **kwargs):
        final_dict = {}
        for log_value in obj.log_values:
            value = log_value.text_value if log_value.text_value else log_value.numeric_value
            final_dict[log_value.parameter_id] = value

        return final_dict
