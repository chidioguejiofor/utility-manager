from .base import BaseModel, IDGenerator
from .membership import Membership, Role
from settings import db
import enum


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

    @classmethod
    def bulk_create(cls, iterable):
        """Bulk creates the organisations and their corresponding Membership

        Args:
            iterable:

        Returns:
            list: a list of organisation models
        """
        org_objs = super().bulk_create(iterable)
        memberships = []
        for org_obj in org_objs:
            memberships.append(
                Membership(
                    user_id=org_obj.creator_id,
                    organisation_id=org_obj.id,
                    role=Role.OWNER,
                ))
        Membership.bulk_create(memberships)
        return org_objs

    def after_save(self):
        from api.services.file_uploader import FileUploader

        Membership(organisation_id=self.id,
                   user_id=self.creator_id,
                   role=Role.OWNER).save(commit=True)
        if self.logo:
            self.filename = f'dumped_files/{self.creator_id}-organisation.jpg'
            self.logo.save(dst=self.filename)
            FileUploader.upload_file.delay(self.id, 'Organisation',
                                           self.filename)
