from settings import db
from .base import OrgBaseModel, UserActionBase, BaseModel
import enum
from api.utils.constants import ID_FIELD_LENGTH


class TokenType(enum.Enum):
    CONSTANT = 'CONSTANT'
    PARAMETER = 'PARAMETER'
    SYMBOL = 'SYMBOL'
    FORMULA = 'FORMULA'


class MathOperation(enum.Enum):
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


class Formula(UserActionBase, OrgBaseModel):
    name = db.Column(db.String(30), nullable=False)
    has_formula = db.Column(db.Boolean, nullable=False)

    # Relationships
    tokens = db.relationship("FormulaToken",
                             back_populates='parent',
                             lazy=True)
    referenced_tokens = db.relationship("FormulaToken",
                                        back_populates='referenced_formula',
                                        lazy=True)


class FormulaToken(UserActionBase, OrgBaseModel):
    # Token values
    position = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum(TokenType, name='token_type_enum'),
                     nullable=False)

    value_from = db.Column(db.Enum(TokenValueFrom,
                                   name='token_value_from_enum'),
                           nullable=False,
                           default=TokenValueFrom.CURRENT)

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
