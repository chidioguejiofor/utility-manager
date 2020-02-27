from .custom_fields import *
from marshmallow import Schema, post_load, EXCLUDE


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
    created_by_id = StringField()
    updated_by_id = StringField()
