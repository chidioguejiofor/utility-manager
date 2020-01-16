from settings import db
from .base import BaseModel


class Role(BaseModel):
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.TEXT)
    __unique_constraints__ = (('name', 'role_name_constraint'), )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = self.name.upper()
