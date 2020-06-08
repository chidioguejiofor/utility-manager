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
    sections = db.relationship("ReportSection",
                               back_populates='report',
                               lazy=True)


class ReportSection(BaseModel):
    name = db.Column(db.String(), nullable=False)
    report_id = db.Column(db.String(),
                          db.ForeignKey('Report.id', ondelete='CASCADE'),
                          nullable=False)
    appliance_id = db.Column(db.String(),
                             db.ForeignKey('Appliance.id', ondelete='CASCADE'),
                             nullable=False)
    columns = db.relationship("ReportColumn",
                              back_populates='report_section',
                              lazy=True)
    report = db.relationship("Report", back_populates='sections', lazy=True)


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

    report_section = db.relationship("ReportSection",
                                     back_populates='columns',
                                     lazy=True)
    parameter = db.relationship("Parameter", lazy=True)
