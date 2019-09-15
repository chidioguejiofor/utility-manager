import re
from marshmallow import fields, ValidationError
from api.utils.error_messages import serialization_error


class FieldValidator:
    def __init__(self, min_length=0, max_length=0, *args, **kwargs):
        validator_list = (self._get_min_length_validator(min_length) +
                          self._get_max_length_validator(max_length) +
                          kwargs.pop('validate', []))

        super().__init__(
            validate=validator_list,
            *args,
            **kwargs,
        )

    @staticmethod
    def _get_min_length_validator(min_length):
        def _validator(data):
            if len(data) < min_length:
                raise ValidationError(
                    message=
                    f'This field must be greater than {min_length} characters')

        return [_validator] if not min_length else []

    @staticmethod
    def _get_max_length_validator(max_length):
        if not max_length:
            return []

        def _validator(data):
            if len(data) > max_length:
                raise ValidationError(
                    message=
                    f'This field must be less than {max_length} characters')

        return [_validator]


class StringField(FieldValidator, fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        data = super()._deserialize(value, attr, data, **kwargs)
        return data.strip()


class RegexField(StringField):
    def __init__(self, regex, regex_message, *args, **kwargs):
        validations = kwargs.get('validate', [])
        regex_validator = self._get_regex_validator(regex, regex_message)
        validations = validations + regex_validator
        super().__init__(*args, validate=validations, **kwargs)

    @staticmethod
    def _get_regex_validator(regex, message='Field does not match pattern'):
        def _validator(data):
            if re.match(regex, data) is None:
                raise ValidationError(message=message)

        return [_validator] if regex else []


class AlphanumericField(RegexField):
    def __init__(self, allow_spaces=False, *args, **kwargs):
        regex = '^[A-Za-z0-9]+$'

        if allow_spaces:
            regex = '^[A-Za-z0-9\\s]+$'
        super().__init__(regex=regex,
                         regex_message=serialization_error['alpha_numeric'],
                         *args,
                         **kwargs)
