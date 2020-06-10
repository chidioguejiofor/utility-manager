from marshmallow import fields, validates_schema, ValidationError, post_load
from marshmallow_enum import EnumField
from .base import (AbstractSchemaWithTimeStampsMixin, ListField,
                   AlphanumericField, BaseSchema, IDField, AlphaOnlyField)
from ..models import (Formula as FormulaModel, FormulaToken as
                      FormulaTokenModel, TokenTypeEnum, TokenValueFromEnum,
                      MathSymbolEnum)
from .unit import Unit
from .parameter import Parameter
from api.utils.error_messages import formula_errors
from api.utils.constants import (GENERIC_EXCLUDE_ORG_AND_USER_AUDIT_FIELDS,
                                 GENERIC_EXCLUDE_SCHEMA_FIELDS_AND_ORG,
                                 GENERIC_EXCLUDE_SCHEMA_FIELDS)


class FormulaToken(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = FormulaTokenModel
    position = fields.Integer(dump_only=True)
    type = EnumField(enum=TokenTypeEnum, by_value=True, required=True)

    value_from = EnumField(enum=TokenValueFromEnum,
                           data_key='valueFrom',
                           by_value=True)
    symbol = EnumField(
        enum=MathSymbolEnum,
        # dump_only=True,
        data_key='symbol',
        by_value=True,
    )
    parent_id = IDField(load_only=True)
    # values
    constant = fields.Number()
    formula_id = IDField(load_only=True)
    parameter_id = IDField(load_only=True)
    # nested fields
    param_exclude = GENERIC_EXCLUDE_ORG_AND_USER_AUDIT_FIELDS + [
        'editable', 'validation'
    ]
    parameter = fields.Nested(Parameter(exclude=param_exclude), dump_only=True)

    @validates_schema
    def validate_formula_token(self, data, **kwargs):
        """This enforces some required keys based on the specified type

        Args:
            data:
            **kwargs:

        Returns:

        """
        token_type = data.get('type')

        if token_type == TokenTypeEnum.SYMBOL and not data.get('symbol'):
            raise ValidationError({
                'symbol':
                [formula_errors['required_field_for_type'].format('SYMBOL')]
            })
        if token_type == TokenTypeEnum.PARAMETER and data.get(
                'parameter_id') is None:
            raise ValidationError({
                'parameter_id': [
                    formula_errors['required_field_for_type'].format(
                        'PARAMETER')
                ]
            })
        if token_type == TokenTypeEnum.FORMULA and data.get(
                'formula_id') is None:
            raise ValidationError({
                'formula_id':
                [formula_errors['required_field_for_type'].format('FORMULA')]
            })
        if token_type == TokenTypeEnum.CONSTANT and data.get(
                'constant') is None:
            raise ValidationError({
                'constant':
                [formula_errors['required_field_for_type'].format('CONSTANT')]
            })
        return data

    @post_load
    def map_data_based_on_specified_type(self, data, **kwargs):
        """This sets fields that would not be used in the app based on type

        When the type is TokenTypeEnum.SYMBOL it takes only the symbol value and sets others to null
        When the type is TokenTypeEnum.PARAMETER  it takes only the parameter_id as sets other values to null
        ..and so on

        Args:
            data (FormulaTokenModel): The FormulaToken model that represents the data sent from the user
            **kwargs:

        Returns:

        """

        data.value_from = data.value_from if data.value_from else TokenValueFromEnum.CURRENT
        if data.type == TokenTypeEnum.SYMBOL:
            data.formula_id = data.parameter_id = data.constant = data.value_from = None
        elif data.type == TokenTypeEnum.PARAMETER:
            data.formula_id = data.symbol = data.constant = None
        elif data.type == TokenTypeEnum.FORMULA:
            data.parameter_id = data.symbol = data.constant = None
        elif data.type == TokenTypeEnum.CONSTANT:
            data.parameter_id = data.symbol = data.formula_id = data.value_from = None
        return data


class Formula(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = FormulaModel
    name = AlphaOnlyField(required=True,
                          min_length=2,
                          max_length=30,
                          allow_spaces=True)
    tokens = ListField(fields.Nested(
        FormulaToken(exclude=GENERIC_EXCLUDE_SCHEMA_FIELDS)),
                       min_length=1)
    unit_id = IDField(data_key='unitId', load_only=True)
    unit = fields.Nested(Unit,
                         dump_only=True,
                         exclude=GENERIC_EXCLUDE_SCHEMA_FIELDS_AND_ORG)
