from .base import AbstractSchemaWithTimeStampsMixin, AbstractUserActionMixin, AlphanumericField, BaseSchema, StringField
from marshmallow import fields, post_load
from api.utils.error_messages import parameter_errors
from api.utils.exceptions import ResponseException
from marshmallow_enum import EnumField
from ..models import Parameter as ParameterModel, ValueTypeEnum
from api.utils.constants import GENERIC_EXCLUDE_SCHEMA_FIELDS, GENERIC_EXCLUDE_USER_AUDIT_FIELDS
from .unit import Unit
import dateutil.parser


class Parameter(AbstractUserActionMixin, AbstractSchemaWithTimeStampsMixin,
                BaseSchema):
    __model__ = ParameterModel
    name = AlphanumericField(allow_spaces=True, required=True, capitalize=True)
    created_by_id = StringField(load_only=True, data_key='createdById')
    updated_by_id = StringField(load_only=True, data_key='updated_by_id')
    unit_id = StringField(load_only=True, data_key='unitId')
    validation = StringField()
    value_type = EnumField(enum=ValueTypeEnum,
                           data_key='valueType',
                           by_value=False,
                           required=True)
    organisation_id = StringField(data_key='organisationId', required=True)
    editable = fields.Function(lambda obj: bool(obj.organisation_id),
                               dump_only=True)
    unit = fields.Nested(Unit(exclude=GENERIC_EXCLUDE_SCHEMA_FIELDS +
                              ['organisation_id']),
                         dump_only=True)

    def validation_enum_value_type(self, validation):
        self._error_msg_generator(not validation,
                                  'missing_validation_for_type', 'ENUM')
        value_are_more_than_two = len(validation.split(',')) < 2
        self._error_msg_generator(value_are_more_than_two,
                                  'enum_has_one_field')

    def _error_msg_generator(self, should_throw_error, err_key, *args):
        if should_throw_error:
            raise ResponseException(
                message=parameter_errors[err_key].format(*args),
                status_code=400,
            )

    def validate_non_enum_value_type(self, value_type, validation_str):
        splitted = validation_str.split(',')
        settings = {
            'gte': 0,
            'gt': 0,
            'lte': 0,
            'lt': 0,
        }
        length_is_valid = len(splitted) > 4
        self._error_msg_generator(length_is_valid, 'invalid_validations')

        for validation_arg in splitted:
            slitted_single_validation = validation_arg.strip().split(' ')
            validation_is_valid = len(slitted_single_validation) != 2
            self._error_msg_generator(validation_is_valid,
                                      'invalid_validation_format',
                                      validation_arg)
            key, value = slitted_single_validation
            key_exists = key in settings
            self._error_msg_generator(not key_exists, 'invalid_validation_key',
                                      key)
            many_values_for_key = settings[key] > 0
            self._error_msg_generator(many_values_for_key,
                                      'multiple_validation_for_key', key)

            if value_type == ValueTypeEnum.NUMERIC:
                try:
                    float(value)
                except ValueError:
                    self._error_msg_generator(True, 'value_not_a_number',
                                              value, validation_arg)
            elif value.isdecimal():
                self._error_msg_generator(True, 'number_not_a_date',
                                          value_type.name, validation_arg)
            else:
                try:
                    dateutil.parser.parse(value)
                except Exception:
                    self._error_msg_generator(True, 'invalid_date', value)
            settings[key] += 1

    @post_load
    def create_objects(self, data, **kwargs):
        validation_str = data.get('validation', '')
        value_type = data['value_type']
        if validation_str:
            data['validation'] = validation_str = validation_str.replace(
                ', ', ',')
        if value_type == ValueTypeEnum.ENUM:
            self.validation_enum_value_type(validation_str)
        elif len(validation_str) > 0:
            self.validate_non_enum_value_type(value_type, validation_str)
        return super().create_objects(data, **kwargs)


class ApplianceParameter(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    param_exclude = GENERIC_EXCLUDE_USER_AUDIT_FIELDS + [
        'organisation_id', 'editable'
    ]
    required = fields.Boolean(dump_only=True)
    parameter = fields.Nested(Parameter(exclude=param_exclude), dump_only=True)
