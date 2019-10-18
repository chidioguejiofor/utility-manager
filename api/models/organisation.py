from .base import BaseModel
from .membership import Membership, Role
from settings import db
import enum

from sqlalchemy import event


class Subscription(enum.Enum):
    FREE = 'FREE'
    BRONZE = 'BRONZE'
    SILVER = 'SILVER'
    GOLD = 'GOLD'
    DIAMOND = 'DIAMOND'


class Organisation(BaseModel):
    name = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    subscription_type = db.Column(db.Enum(Subscription),
                                  nullable=False,
                                  default=Subscription.FREE)
    creator_id = db.Column(db.String(21),
                           db.ForeignKey('User.id'),
                           nullable=False)
    memberships = db.relationship('Membership',
                                  back_populates='organisation',
                                  lazy=True)
    image_public_id = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    creator = db.relationship('User')
    filename = None
    logo = None
    __unique_constraints__ = (('website', 'org_unique_website_constraint'), )


@event.listens_for(Organisation, 'after_insert')
def send_verification_email(mapper, connect, target):
    from api.services.file_uploader import FileUploader
    Membership(organisation_id=target.id,
               user_id=target.creator_id,
               role=Role.OWNER).save(commit=False)
    if target.logo:
        FileUploader.upload_file.delay(target.id, 'Organisation',
                                       target.filename)
