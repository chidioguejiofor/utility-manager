from sqlalchemy import exc, event
from settings import db
from api.utils.exceptions import ModelOperationException
from api.utils.error_messages import serialization_error
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
    image_public_id = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)
    filename = image = _password = None
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

    def update(self, *args, **kwargs):
        try:
            super().update(*args, **kwargs)
        except exc.IntegrityError:
            db.session.rollback()
            raise ModelOperationException(
                serialization_error['already_exists'].format('username'),
                serialization_error['already_exists'].format('username'),
                status_code=409,
            )

    def after_update(self, *args, **kwargs):
        from api.services.file_uploader import FileUploader
        if self.image:
            self.filename = f'dumped_files/{self.id}-user.jpg'
            self.image.save(dst=self.filename)
            FileUploader.upload_file.delay(self.id, 'User', self.filename,
                                           self.image_public_id)


@event.listens_for(User, 'after_insert')
def send_verification_email(mapper, connection, target):
    from api.utils.emails import EmailUtil
    if target.redirect_url:
        EmailUtil.send_verification_email_to_user(target)
