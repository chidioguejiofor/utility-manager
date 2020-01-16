from api.models import Role
from api.models.base.id_generator import IDGenerator
from .base import BaseSeeder


class RoleSeed(BaseSeeder):
    __model__ = Role
    KEY = 'role'

    def __init__(self, name, description, **kwargs):
        super().__init__(**kwargs)
        pk = kwargs.get('id')
        self.id = pk if pk else IDGenerator.generate_id()
        self.name = name.upper()
        self.description = description

    def __eq__(self, other):
        return self.name.upper() == other.name.upper()

    def model_filter(self):
        return self.__model__.name == self.name

    def __repr__(self):
        return "%s(name=%r, description=%r, created_at=%s, updated_at=%s)" % (
            self.__class__.__name__,
            self.name,
            self.description,
            self.created_at,
            self.updated_at,
        )

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
