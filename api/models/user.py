from settings import db
from .base import BaseModel


class User(BaseModel):
    name = db.Column(db.String(128))
