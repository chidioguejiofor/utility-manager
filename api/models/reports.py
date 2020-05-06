import enum
from settings import db
from .base import OrgBaseModel, BaseModel, UserActionBase


class AggregationType(enum.Enum):
    SUMMATION = 'SUM'
    AVERAGE = 'AVG'
    MINIMUM = 'MIN'
    MAXIMUM = 'MAX'


class Report(OrgBaseModel, UserActionBase):
    _IS_CREATED_BY_NULLABLE = _ORG_ID_NULLABLE = False
    name = db.Column(db.String(), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)


class ReportSection(BaseModel):
    name = db.Column(db.String(), nullable=False)
    report_id = db.Column(db.String(),
                          db.ForeignKey('Report.id', ondelete='CASCADE'),
                          nullable=False)
    appliance_id = db.Column(db.String(),
                             db.ForeignKey('Appliance.id', ondelete='CASCADE'),
                             nullable=False)


class ReportColumn(BaseModel):
    report_section_id = db.Column(db.String(),
                                  db.ForeignKey('ReportSection.id',
                                                ondelete='CASCADE'),
                                  nullable=False)
    formula_id = db.Column(db.String(), nullable=True)
    parameter_id = db.Column(
        db.String(22),
        db.ForeignKey('Parameter.id', ondelete='CASCADE'),
    )
    aggregation_type = db.Column(
        db.Enum(AggregationType, name='aggregation_type_enum'),
        nullable=False,
        default=AggregationType.AVERAGE,
    )
    aggregate_by_column = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )
