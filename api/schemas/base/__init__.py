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
        return self.__model__(**data)

    def dump_success_data(self, model_obj, message=None, **kwargs):
        dump_data = {
            'status': 'success',
            'data': self.dump(model_obj, **kwargs),
            'message': message
        }
        return dump_data


class AbstractSchemaWithTimeStampsMixin:
    created_at = fields.DateTime(data_key='createdAt', dump_only=True)
    updated_at = fields.DateTime(data_key='updatedAt', dump_only=True)
