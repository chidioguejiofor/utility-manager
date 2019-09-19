from settings import db
from passlib.hash import pbkdf2_sha512
from .base import BaseModel


class User(BaseModel):
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    password_hash = db.Column(db.VARCHAR(130), nullable=False)
    verified = db.Column(db.BOOLEAN, default=False, nullable=False)
    _password = None
    memberships = db.relationship('Membership',
                                  back_populates='member',
                                  lazy=True)
    organisations = None
    __table_args__ = (db.UniqueConstraint(
        'email', name='user_email_unique_constraint'), )

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password_str):
        self._password = password_str
        self.password_hash = pbkdf2_sha512.hash(password_str)

    def verify_password(self, password_str):
        return pbkdf2_sha512.verify(password_str, self.password_hash)
