from settings import db
from .base import BaseModel


class User(BaseModel):
    __tablename__ = "User"
    name = db.Column(db.String(128))
