import re
from marshmallow import fields, ValidationError
from api.utils.error_messages import serialization_error
from werkzeug.datastructures import FileStorage


class FieldValidator:
    def __init__(self, min_length=None, max_length=None, *args, **kwargs):
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
                    message=serialization_error['min_length_error'].format(
                        min_length))

        return [_validator] if min_length else []

    @staticmethod
    def _get_max_length_validator(max_length):
        def _validator(data):
            if len(data) > max_length:
                raise ValidationError(
                    message=serialization_error['max_length_error'].format(
                        max_length))

        return [_validator] if max_length else []


class StringField(FieldValidator, fields.String):
    def __init__(self, *args, capitalize=False, **kwargs):
        self.capitalize = capitalize
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        """This method is called when data is being loaded to python

        It removes the all surrounding spaces and changes double spaces to one space

b
        Args:
            value: value send from user
            attr: the field name
            data:  The raw input data passed to the Schema.load.
            **kwargs: Field-specific keyword arguments.

        Returns:
            (str):  A deserialized value with no double-space

        """
        des_value = super()._deserialize(value, attr, data, **kwargs)

        des_value = re.sub("\\s{2,}", " ", des_value.strip())
        return des_value.capitalize() if self.capitalize else des_value


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


class AlphaOnlyField(StringField):
    def __init__(self, *args, **kwargs):
        validations = kwargs.get('validate', [])
        validator = self._get_alpha_validator()
        validations = validations + validator
        super().__init__(*args, validate=validations, **kwargs)

    @staticmethod
    def _get_alpha_validator():
        def _validator(data):
            if not data.strip().isalpha():
                raise ValidationError(
                    message=serialization_error['alpha_only'])

        return [_validator]


class ImageField(fields.Raw):
    def __init__(self, *args, **kwargs):
        validations = kwargs.get('validate', [])
        validator = self._get_image_validator()
        validations = validations + validator
        super().__init__(*args, validate=validations, **kwargs)

    @staticmethod
    def _get_image_validator():
        def _validator(data):
            if not (isinstance(data, FileStorage)
                    and 'image/' in data.mimetype):
                raise ValidationError(
                    message=serialization_error['invalid_image'])

        return [_validator]
