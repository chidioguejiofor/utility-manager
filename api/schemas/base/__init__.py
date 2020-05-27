from .custom_fields import *
from marshmallow import Schema, post_load, EXCLUDE
from api.utils.constants import EXCLUDE_USER_SCHEMA_FIELDS


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    __model__ = None
    id = StringField(dump_only=True)

    @post_load
    def create_objects(self, data, **kwargs):
        if self.__model__:
            return self.__model__(**data)
        return data

    def dump_success_data(self, model_obj, message=None, **kwargs):
        dump_data = {
            'status': 'success',
            'message': message,
            'data': self.dump(model_obj, **kwargs),
        }
        return dump_data


class AbstractSchemaWithTimeStampsMixin:
    created_at = fields.DateTime(data_key='createdAt', dump_only=True)
    updated_at = fields.DateTime(data_key='updatedAt', dump_only=True)


class AbstractUserActionMixin:
    from ..user import User
    created_by_id = StringField(load_only=True)
    updated_by_id = StringField(load_only=True)
    created_by = fields.Nested(User(exclude=EXCLUDE_USER_SCHEMA_FIELDS),
                               dump_only=True,
                               data_key='createdBy')
    updated_by = fields.Nested(User(exclude=EXCLUDE_USER_SCHEMA_FIELDS),
                               dump_only=True,
                               data_key='updatedBy')
