from settings import db
from api.utils.time_util import TimeUtil
from api.utils.error_messages import serialization_error
from api.utils.exceptions import UniqueConstraintException
from sqlalchemy.ext.declarative import declared_attr, as_declarative


class BaseModel(db.Model):
    __abstract__ = True
    __unique_constraints__ = []

    @declared_attr
    def __tablename__(cls):
        return cls.__name__

    @declared_attr
    def __table_args__(cls):
        final_list = []
        for column, constraint_name in cls.__unique_constraints__:
            final_list.append(db.UniqueConstraint(column,
                                                  name=constraint_name))
        return tuple(final_list)

    id = db.Column(
        db.String(21),
        primary_key=True,
    )
    created_at = db.Column(db.DateTime(timezone=True), default=TimeUtil.now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def save(self):
        self._valid_unique_constraints(self)
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def _valid_unique_constraints(cls, obj):
        filter_query = None
        cols = []
        for unique_column, _ in cls.__unique_constraints__:
            test = getattr(cls, unique_column) == getattr(obj, unique_column)
            if filter_query is None:
                filter_query = test
            else:
                filter_query = filter_query | test
            cols.append(unique_column)

        if cls.query.filter(filter_query).count() >= 1:
            cols = ' or '.join(cols)
            raise UniqueConstraintException(
                serialization_error['already_exists'].format(cols))

    @staticmethod
    def update():
        db.session.commit()

    @classmethod
    def update_query(cls, query, **kwargs):
        """Updates models that meet a condition

        Filters the base model by a condition and updates it with the
        kwargs specified

        Args:
            query(SQLAlchemy Query): The query to be updated.
            kwargs: The keyword representation of the updates

        Returns:

        """
        return query.update(kwargs)
