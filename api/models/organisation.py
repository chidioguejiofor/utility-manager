import os
from .base import BaseModel
from .membership import Membership
from settings import db
from api.utils.error_messages import serialization_error
import enum


class Subscription(enum.Enum):
    FREE = 'FREE'
    BRONZE = 'BRONZE'
    SILVER = 'SILVER'
    GOLD = 'GOLD'
    DIAMOND = 'DIAMOND'


class Organisation(BaseModel):
    __unique_violation_msg__ = serialization_error['already_exists'].format(
        'Website')
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
        from api.services.redis_util import RedisUtil
        org_objs = super().bulk_create(iterable)
        memberships = []
        for org_obj in org_objs:
            memberships.append(
                Membership(
                    user_id=org_obj.creator_id,
                    organisation_id=org_obj.id,
                    role_id=RedisUtil.get_role_id('OWNER'),
                ))
        Membership.bulk_create(memberships)
        return org_objs

    def after_save(self):
        from api.services.file_uploader import FileUploader
        from api.services.redis_util import RedisUtil
        Membership(organisation_id=self.id,
                   user_id=self.creator_id,
                   role_id=RedisUtil.get_role_id('OWNER')).save(commit=True)
        if self.logo:
            path_sep = os.path.sep
            self.filename = f'dumped_files{path_sep}{self.creator_id}-organisation.png'
            self.logo.save(dst=self.filename)
            FileUploader.upload_file.delay(self.id, 'Organisation',
                                           self.filename)
