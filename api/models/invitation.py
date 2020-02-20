from settings import db
from .base import OrgBaseModel
from api.utils.constants import APP_EMAIL


class Invitation(OrgBaseModel):
    _ORG_ID_NULLABLE = False
    email = db.Column(db.String(320), nullable=False)
    role_id = db.Column(db.String(21),
                        db.ForeignKey('Role.id'),
                        nullable=False)
    user_dashboard_url = db.Column(db.TEXT, nullable=False)
    signup_url = db.Column(db.TEXT, nullable=False)
    role = db.relationship('Role')

    __unique_constraints__ = ((('email', 'organisation_id'),
                               'invitation_email_org_constraint'), )

    @classmethod
    def bulk_create(cls, iterable, *args, **kwargs):

        commit = kwargs.get('commit', None)
        return super().bulk_create(iterable, *args, commit=commit, **kwargs)

    @classmethod
    def after_bulk_create(cls,
                          model_objs,
                          *,
                          inviter_membership=None,
                          commit=None,
                          send_email=False,
                          signup_url=None,
                          dashboard_url=None):
        """Called after bulk create and sends mail to the user based on the arguments specified

        Args:
            model_objs([BaseModel]): This is the list of models that was created

        Keyword Args:
            inviter_membership (Membership): contains membership information of the user that is making the request
            commit(bool|None): When this is set to True or None(ie not specified), the Invitations would be commited to
            the database. Otherwise, they would just be added to the session

            send_email(bool): When True, invitation emails would be sent to the users.
                By default this has a value of False, when
            signup_url: The place to redirect the user to in case he does not have an account
            dashboard_url: The place to redirect the user would click when he has an account

        """

        if not model_objs:
            return
        if not send_email:
            if commit is True or commit is None:
                db.session.commit()
            return
        emails = [model_obj.email for model_obj in model_objs]
        cls.send_email_to_users(dashboard_url, inviter_membership, emails,
                                signup_url)
        if commit is True or commit is None:
            db.session.commit()

    @classmethod
    def send_email_to_users(cls, dashboard_url, inviter_membership, emails,
                            signup_url):
        from api.utils.emails import EmailUtil

        mail_kwargs = {
            'organisation_name': inviter_membership.organisation.name,
            'user_first_name': inviter_membership.member.first_name,
            'user_last_name': inviter_membership.member.last_name,
            'dashboard_link': dashboard_url,
            'signup_link': signup_url,
        }
        html = EmailUtil.extract_html_from_template('org-invitation-email',
                                                    **mail_kwargs)
        subject = "Invitation to Organisation"
        EmailUtil.send_mail_as_html.delay(subject,
                                          APP_EMAIL,
                                          html,
                                          blind_copies=emails)
