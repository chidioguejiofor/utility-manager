from sqlalchemy import event
from settings import db
from passlib.hash import pbkdf2_sha512
from .base import BaseModel


class User(BaseModel):

    username = db.Column(
        db.String(20),
        nullable=False,
    )
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    password_hash = db.Column(db.VARCHAR(130), nullable=False)
    verified = db.Column(db.BOOLEAN, default=False, nullable=False)
    _password = None
    memberships = db.relationship('Membership',
                                  back_populates='member',
                                  lazy=True)
    owned_organisations = db.relationship('Organisation',
                                          back_populates='creator')
    created_parameters = db.relationship(
        'Parameter',
        lazy='dynamic',
        foreign_keys='Parameter.created_by_id',
        back_populates='created_by')
    updated_parameters = db.relationship(
        'Parameter',
        lazy='dynamic',
        foreign_keys='Parameter.updated_by_id',
        back_populates='updated_by')

    organisations = None
    redirect_url = None
    __unique_constraints__ = (('email', 'user_email_unique_constraint'),
                              ('username', 'username_unique_constraint'))

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password_str):
        self._password = password_str
        self.password_hash = pbkdf2_sha512.hash(password_str)

    def verify_password(self, password_str):
        return pbkdf2_sha512.verify(password_str, self.password_hash)


@event.listens_for(User, 'after_insert')
def send_verification_email(mapper, connection, target):
    from api.utils.emails import EmailUtil
    if target.redirect_url:
        EmailUtil.send_verification_email_to_user(target)
