from settings import db
from .base import OrgBaseModel, UserActionBase, BaseModel
import enum
import numpy as np
from api.utils.constants import ID_FIELD_LENGTH
from api.utils.error_messages import serialization_error
from sqlalchemy.orm import joinedload


class TokenType(enum.Enum):
    CONSTANT = 'CONSTANT'
    PARAMETER = 'PARAMETER'
    SYMBOL = 'SYMBOL'
    FORMULA = 'FORMULA'


class MathSymbol(enum.Enum):
    MULTIPLY = '*'
    SUBTRACT = '-'
    DIVISION = '/'
    ADDITION = '+'
    OPEN_BRACKET = '('
    CLOSE_BRACKET = ')'


class TokenValueFrom(enum.Enum):
    PREV = 'PREV'  # this would indicate that the value is coming from the previous row in report/data
    CURRENT = 'CURRENT'  # this indicates that the value is coming from the current row in the report/data


class DateAggregator(BaseModel):
    name = db.Column(db.String(35), nullable=False)
    sql_func_call = db.Column(db.TEXT, nullable=False)


class FormulaToken(UserActionBase, OrgBaseModel):
    # Token values
    position = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum(TokenType, name='token_type_enum'),
                     nullable=False)

    value_from = db.Column(db.Enum(TokenValueFrom,
                                   name='token_value_from_enum'),
                           nullable=True)

    # Values including symbols and foreign keys
    symbol = db.Column(
        db.Enum(MathSymbol, name='math_symbol_enum'),
        nullable=True,
    )

    constant = db.Column(db.Float(precision=2), nullable=True)
    # Foreign Keys
    parent_id = db.Column(
        db.String(ID_FIELD_LENGTH),  # The formula that owns this token
        db.ForeignKey('Formula.id', ondelete='CASCADE'),
        nullable=False)

    formula_id = db.Column(db.String(ID_FIELD_LENGTH),
                           db.ForeignKey('Formula.id', ondelete='CASCADE'),
                           nullable=True)
    parameter_id = db.Column(db.String(ID_FIELD_LENGTH),
                             db.ForeignKey('Parameter.id', ondelete='CASCADE'),
                             nullable=True)

    # Relationships
    parent = db.relationship("Formula",
                             back_populates='tokens',
                             foreign_keys=[parent_id],
                             lazy=True)

    parameter = db.relationship("Parameter", lazy=True)
    referenced_formula = db.relationship("Formula",
                                         back_populates='referenced_tokens',
                                         foreign_keys=[formula_id],
                                         lazy=True)


class Formula(UserActionBase, OrgBaseModel):
    name = db.Column(db.String(30), nullable=False)
    has_formula = db.Column(db.Boolean, nullable=False)
    unit_id = db.Column(db.String(ID_FIELD_LENGTH),
                        db.ForeignKey('Unit.id',
                                      ondelete='CASCADE',
                                      name='unit_id_fk'),
                        nullable=True)

    # Relationships
    tokens = db.relationship("FormulaToken",
                             back_populates='parent',
                             foreign_keys=[FormulaToken.parent_id],
                             lazy=True)
    referenced_tokens = db.relationship("FormulaToken",
                                        back_populates='referenced_formula',
                                        foreign_keys=[FormulaToken.formula_id],
                                        lazy=True)
    unit = db.relationship("Unit", lazy=True)

    # Unique Constraints
    __unique_constraints__ = ((('name', 'organisation_id'),
                               'org_formula_unique_constraint'), )
    __unique_violation_msg__ = serialization_error['exists_in_org'].format(
        'Formula')
