from marshmallow import fields
from .base import (AbstractSchemaWithTimeStampsMixin, BaseSchema, StringField,
                   AbstractUserActionMixin, ListField, IDField)
from .appliance_category import ApplianceCategory


class Appliance(BaseSchema, AbstractSchemaWithTimeStampsMixin,
                AbstractUserActionMixin):
    _exclude_category_cols = [
        'created_at', 'updated_at', 'editable', 'created_by', 'updated_by'
    ]
    appliance_category_id = IDField(required=True,
                                    data_key='categoryId',
                                    load_only=True)
    appliance_category = fields.Nested(
        ApplianceCategory(exclude=_exclude_category_cols),
        dump_only=True,
        data_key='category')
    label = StringField(max_length=50,
                        min_length=2,
                        required=True,
                        capitalize=True)
    specs = fields.Dict(required=True)
    parameters = ListField(IDField, min_length=1, required=True)
    required_parameters = ListField(IDField,
                                    min_length=1,
                                    data_key='requiredParameters')
