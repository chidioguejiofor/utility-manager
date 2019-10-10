from .custom_fields import *
from marshmallow import Schema, post_load, pre_load


class BaseSchema(Schema):
    __model__ = None
    id = StringField(dump_only=True)

    @post_load
    def create_objects(self, data, **kwargs):
        return self.__model__(**data)

    def dump_success_data(self, model_obj, message=None):
        dump_data = {
            'status': 'success',
            'data': self.dump(model_obj),
        }
        if message:
            dump_data['message'] = message
        return dump_data


class AbstractSchemaWithTimeStampsMixin:
    created_at = fields.DateTime(data_key='createdAt', dump_only=True)
    updated_at = fields.DateTime(data_key='updatedAt', dump_only=True)
