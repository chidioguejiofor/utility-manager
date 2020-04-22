from marshmallow import fields
from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, ListField, IDField)


class Log(BaseSchema, AbstractSchemaWithTimeStampsMixin,
          AbstractUserActionMixin):
    appliance_id = StringField()
    log_values = fields.Method('retrieve_log_value', data_key='logValues')

    def retrieve_log_value(self, obj, **kwargs):
        return {
            log_value.parameter_id: log_value.value
            for log_value in obj.log_values
        }
