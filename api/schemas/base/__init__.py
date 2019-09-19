from .custom_fields import *
from marshmallow import Schema, post_load


class BaseSchema(Schema):
    __model__ = None
    id = StringField(dump_only=True)

    @post_load
    def create_objects(self, data, **kwargs):
        return self.__model__(**data)


class AbstractSchemaWithTimeStamps(BaseSchema):
    created_at = fields.DateTime(data_key='createdAt', dump_only=True)
    updated_at = fields.DateTime(data_key='updatedAt', dump_only=True)
