from settings import db
from enum import Enum
from .base import BaseModel


class Membership(BaseModel):
    user_id = db.Column(db.String(21), db.ForeignKey('User.id'))
    organisation_id = db.Column(db.String(21),
                                db.ForeignKey('Organisation.id'))
    role_id = db.Column(
        db.String(21),
        db.ForeignKey('Role.id'),
        nullable=False,
    )
    role = db.relationship("Role")
    member = db.relationship("User", back_populates="memberships")
    organisation = db.relationship('Organisation',
                                   back_populates='memberships')
    __unique_constraints__ = ((('user_id', 'organisation_id'),
                               'membership_user_id_organisation_id_key'), )
