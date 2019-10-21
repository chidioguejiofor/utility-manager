from settings import db
from api.utils.time_util import TimeUtil
from api.utils.error_messages import serialization_error
from api.utils.exceptions import UniqueConstraintException
from sqlalchemy.ext.declarative import declared_attr, as_declarative
import numpy as np


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
            if isinstance(column, tuple):
                final_list.append(
                    db.UniqueConstraint(*column, name=constraint_name))
            else:
                final_list.append(
                    db.UniqueConstraint(column, name=constraint_name))
        return tuple(final_list)

    id = db.Column(
        db.String(21),
        primary_key=True,
    )
    created_at = db.Column(db.DateTime(timezone=True), default=TimeUtil.now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def save(self, commit=True):
        """Saves a new model to the session

        If commit is True it updates the database with new changes else it saves it just
        adds the this model to the session

        When commit is True and an exception occurs, an attempt is made to rollback the current session
        is done before re-raising the exception

        Args:
            commit(bool, optional): If True upates database with model

        Raise:
            sqlalchemy.exc.SQLAlchemyError: when any database error occurs
        """
        self._valid_unique_constraints(self)
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

    @classmethod
    def _compare_column(cls, obj, constraint_col):
        return getattr(cls, constraint_col) == getattr(obj, constraint_col)

    @classmethod
    def _valid_unique_constraints(cls, obj):
        filter_query = None
        cols = []
        for constraint_col, _ in cls.__unique_constraints__:
            if isinstance(constraint_col, tuple):
                test = np.bitwise_and.reduce(
                    [cls._compare_column(obj, col) for col in constraint_col])
                col_msg = f"`{' and '.join(constraint_col)}`"
            else:
                test = cls._compare_column(obj, constraint_col)
                col_msg = f"`{constraint_col}`"
            if filter_query is None:
                filter_query = test
            else:
                filter_query = filter_query | test
            cols.append(col_msg)

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
