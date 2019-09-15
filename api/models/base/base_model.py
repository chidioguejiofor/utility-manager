from settings import db
from api.utils.time_util import TimeUtil
from api.utils.exceptions import ModelsNotOfSameTypeException
from sqlalchemy.ext.declarative import as_declarative, declared_attr


class BaseModel(db.Model):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__

    id = db.Column(
        db.String(21),
        primary_key=True,
    )
    created_at = db.Column(db.DateTime(timezone=True), default=TimeUtil.now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def bulk_create(cls, model_list):
        objects_are_of_same_type = all(
            isinstance(model_obj, cls) for model_obj in model_list)

        if objects_are_of_same_type:
            db.session.bulk_save_objects(model_list)
        else:
            raise ModelsNotOfSameTypeException()

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
