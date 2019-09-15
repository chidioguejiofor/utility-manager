from .base import BaseModel
from settings import db
import enum


class Subscription(enum.Enum):
    FREE = 'FREE'
    BRONZE = 'BRONZE'
    SILVER = 'SILVER'
    GOLD = 'GOLD'
    DIAMOND = 'DIAMOND'


class Organisation(BaseModel):
    name = db.Column(db.String(120), nullable=False, unique=True)
    display_name = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    subscription_type = db.Column(db.Enum(Subscription),
                                  nullable=False,
                                  default=Subscription.FREE)
    logo_url = db.Column(db.String(), nullable=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    password_hash = db.Column(db.TEXT, nullable=True)
