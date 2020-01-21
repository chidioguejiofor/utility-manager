from marshmallow import fields, post_load, ValidationError
from .role import Role
from .organisation import Organisation
from .base import (AbstractSchemaWithTimeStampsMixin, IDField, BaseSchema,
                   StringField, ListField)
from api.utils.error_messages import invitation_errors
from ..models import Invitation as InvitationModel


class Invitation(AbstractSchemaWithTimeStampsMixin, BaseSchema):
    __model__ = InvitationModel
    email = fields.Email(required=True)
    role_id = IDField(data_key='roleId')
    role = fields.Nested(Role)
    user_dashboard_url = StringField(data_key='userDashboardURL')
    signup_url = StringField(data_key='signupURL')
    organisation = fields.Nested(
        Organisation(exclude=['creator', 'subscription_type']))


class InviteUserSchema(BaseSchema):
    __model__ = InvitationModel
    email = fields.Email(required=True)
    role_id = IDField(data_key='roleId')
    role = fields.Nested(Role)
    user_dashboard_url = StringField(data_key='userDashboardURL')
    signup_url = StringField(data_key='signupURL')


class InviteUserSchema(BaseSchema):
    role_id = IDField(required=True, data_key='roleId')
    email = fields.Email(required=True)


class InvitationRequestWithoutInvitesSchema(BaseSchema):
    user_dashboard_url = StringField(required=True,
                                     data_key='userDashboardURL')
    signup_url = StringField(required=True, data_key='signupURL')


class InvitationRequestSchema(InvitationRequestWithoutInvitesSchema):
    def __init__(self, *args, roles_user_cannot_send_invites=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.roles_user_cannot_send_invites = roles_user_cannot_send_invites

    invites = ListField(fields.Nested(InviteUserSchema),
                        min_length=1,
                        required=True)

    INVITE_KEY = 'invites'

    def check_user_dict_input(self, user, index, found_emails):
        error_obj = {}
        role_id_to_be_added = user['role_id']
        user_cannot_add_role = self.roles_user_cannot_send_invites and role_id_to_be_added in self.roles_user_cannot_send_invites
        if user_cannot_add_role:
            role_name = self.roles_user_cannot_send_invites[
                role_id_to_be_added]
            error_obj[str(index)] = {
                'roleId':
                [invitation_errors['cannot_add_role'].format(role_name)]
            }

        if user['email'] in found_emails:
            if str(index) in error_obj:
                error_obj[str(index)]['email'] = [
                    invitation_errors['duplicate_email_in_request']
                ]
            else:
                error_obj[str(index)] = {
                    'email': [invitation_errors['duplicate_email_in_request']],
                }

        return error_obj

    @post_load
    def create_objects(self, data, **kwargs):
        errors = {}
        found_emails = set()
        for index, user in enumerate(data[self.INVITE_KEY]):
            user['signup_url'] = data['signup_url']
            user['user_dashboard_url'] = data['user_dashboard_url']
            error_obj = self.check_user_dict_input(user, index, found_emails)
            if error_obj:
                errors.update(error_obj)
            found_emails.add(user['email'])
        #
        # if len(data[self.INVITE_KEY]) == 0:
        #     errors = ['There must be at least one invite here']

        if errors:
            raise ValidationError({self.INVITE_KEY: errors})

        return data[self.INVITE_KEY]
