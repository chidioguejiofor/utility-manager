from settings import db
from enum import Enum
from .base import BaseModel


class Role(Enum):
    OWNER = 0
    ENGINEER = 1
    MANAGER = 2
    REGULAR_USER = 3


class Membership(BaseModel):
    user_id = db.Column(db.String(21), db.ForeignKey('User.id'))
    organisation_id = db.Column(db.String(21),
                                db.ForeignKey('Organisation.id'))
    role = db.Column(db.Enum(Role), nullable=False, default=Role.REGULAR_USER)
    member = db.relationship("User", back_populates="memberships")
    organisation = db.relationship('Organisation',
                                   back_populates='memberships')
    __table_args__ = (db.UniqueConstraint('user_id', 'organisation_id'), )
