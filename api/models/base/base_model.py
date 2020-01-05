from settings import db
from api.utils.time_util import TimeUtil
from api.utils.error_messages import serialization_error
from api.utils.exceptions import UniqueConstraintException
from sqlalchemy.ext.declarative import declared_attr, AbstractConcreteBase
import numpy as np
from .id_generator import IDGenerator


class BaseModel(db.Model):
    __abstract__ = True
    __unique_constraints__ = []
    __unique_violation_msg__ = None

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

    id = db.Column(db.String(21),
                   primary_key=True,
                   default=IDGenerator.generate_id)
    created_at = db.Column(db.DateTime(timezone=True), default=TimeUtil.now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def before_save(self, *args, **kwargs):
        pass

    def after_save(self, *args, **kwargs):
        pass

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
        self.before_save()
        self._valid_unique_constraints(self)
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

        self.after_save()

    @classmethod
    def _compare_column(cls, obj, constraint_col):
        return getattr(cls, constraint_col) == getattr(obj, constraint_col)

    @classmethod
    def _valid_unique_constraints(cls, obj):
        error_message = cls.__unique_violation_msg__
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
            error_message = (
                error_message if error_message else
                serialization_error['already_exists'].format(cols))
            raise UniqueConstraintException(error_message)

    def before_update(self, *args, **kwargs):
        pass

    def after_update(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        self.before_update(*args, **kwargs)
        db.session.commit()
        self.after_update(*args, **kwargs)

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

    @classmethod
    def bulk_create(cls, iterable):
        """Inserts bulk data into the database using an iterable
        
        Args:
            iterable: An iterable object where each item is either a dict or
                this model_instance

        Returns:
            None: Inserts the data and returns nothing
        """
        model_objs = []
        for data in iterable:
            if not isinstance(data, cls):
                data = cls(**data)
            data.id = data.id if data.id else IDGenerator.generate_id()
            model_objs.append(data)

        db.session.bulk_save_objects(model_objs)
        db.session.commit()
        return model_objs


class UserActionBase(AbstractConcreteBase):
    __back_populates__kwargs__ = None  # should be overriden in concrete class

    @declared_attr
    def created_by_id(cls):
        return db.Column(db.String(21),
                         db.ForeignKey('User.id',
                                       ondelete='RESTRICT',
                                       onupdate='CASCADE'),
                         nullable=True)

    @declared_attr
    def updated_by_id(cls):
        return db.Column(db.String(21),
                         db.ForeignKey('User.id',
                                       ondelete='RESTRICT',
                                       onupdate='CASCADE'),
                         nullable=True)

    @declared_attr
    def created_by(cls):
        return db.relationship(
            'User',
            back_populates=cls.__back_populates__kwargs__['created_by'],
            foreign_keys=[cls.created_by_id])

    @declared_attr
    def updated_by(cls):
        return db.relationship(
            'User',
            back_populates=cls.__back_populates__kwargs__['updated_by'],
            foreign_keys=[cls.updated_by_id])
