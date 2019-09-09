from settings import db
from api.utils.time_util import TimeUtil
from api.utils.exceptions import ModelsNotOfSameTypeException


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(
        db.String(21),
        primary_key=True,
    )
    created_at = db.Column(db.DateTime, default=TimeUtil.now)
    updated_at = db.Column(db.DateTime, nullable=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

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
    def update_by_filter(cls, condition, **kwargs):
        """Updates models that meet a condition

        Filters the base model by a condition and updates it with the
        kwargs specified

        Args:
            condition(SQLAlchemy BinaryExpression): The filter condition.
            kwargs: The keyword representation of the updates

        Returns:

        """
        return cls.query.filter(condition).update(kwargs)
