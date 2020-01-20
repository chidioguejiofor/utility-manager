from .base import BaseView
from settings import endpoint
from flask import request
from api.schemas import InvitationRequestSchema, InvitationSchema
from api.models import Membership, Invitation, db
from api.utils.exceptions import ResponseException
from api.utils.success_messages import INVITING_USER_MSG_DICT
from api.utils.error_messages import invitation_errors, authentication_errors, serialization_error
from api.services.redis_util import RedisUtil
from sqlalchemy import exc, orm


@endpoint('/org/<string:org_id>/invitations')
class OrgInvitations(BaseView):
    protected_methods = ['POST', 'GET']

    def get(self, user_data, org_id):
        pass

    def post(self, user_data, org_id):
        membership = Membership.query.options(
            orm.joinedload('role'), orm.joinedload('organisation'),
            orm.joinedload('member')).filter_by(
                organisation_id=org_id, user_id=user_data['id']).first()

        if not membership:
            raise ResponseException(
                message=serialization_error['not_found'].format(
                    'Organisation id'),
                status_code=404,
            )
        if membership.role.name not in ['OWNER', 'ADMIN']:
            raise ResponseException(
                message=authentication_errors['forbidden'].format('add roles'),
                status_code=403,
            )
        request_data = request.get_json()
        roles_user_cannot_send_invites = self.roles_that_cannot_be_sent_invites_by_current_user(
            membership.role.name)

        invitations = InvitationRequestSchema(
            roles_user_cannot_send_invites=roles_user_cannot_send_invites,
        ).load(request_data)

        email_inputs = [invitation['email'] for invitation in invitations]

        existing_emails = Invitation.query.filter(
            Invitation.email.in_(email_inputs)).all()
        existing_emails = set(inv.email for inv in existing_emails)
        list_of_models = []
        list_of_existing_emails = []
        for inv in invitations:
            if inv['email'] in existing_emails:
                list_of_existing_emails.append({
                    'email':
                    inv['email'],
                    'message':
                    invitation_errors['invites_already_sent_to_email']
                })
            else:
                list_of_models.append(Invitation(**inv,
                                                 organisation_id=org_id))

        invitations = Invitation.bulk_create_or_none(
            list_of_models,
            inviter_membership=membership,
            send_email=True,
            signup_url=request_data['signupURL'],
            dashboard_url=request_data['userDashboardURL'],
        )
        if invitations is None:
            raise ResponseException(
                message=invitation_errors['missing_role_ids'],
                status_code=404,
            )
        res_data = InvitationSchema(many=True,
                                    exclude=['role']).dump(invitations)
        return self.generate_response(list_of_existing_emails, list_of_models,
                                      res_data)

    @staticmethod
    def generate_response(list_of_existing_emails, list_of_models, res_data):
        """Generates response to be sent to the user based on arguments

        When the size of existing emails is equal to that of list_of_models then a status of success is sent
        When the size of  list_of_models os equal to zero, then error is sent
        Otherwise, partial is sent


        Args:
            list_of_existing_emails(list): shows the existing emails specified by the user
            list_of_models(list):  shows the models that were bulk created
            res_data: The response data

        Returns:

        """
        status = 'partial'
        all_succeeded = len(list_of_existing_emails) == 0
        all_failed = len(list_of_models) == 0
        status = 'error' if all_failed else status
        status = 'success' if all_succeeded else status
        status_code = {
            'error': 400,
            'partial': 207,
            'success': 201,
        }
        final_response = {
            'status': status,
            'message': INVITING_USER_MSG_DICT[status],
            'data': {
                'success': res_data,
                'failed': list_of_existing_emails
            }
        }
        return final_response, status_code[status]

    @staticmethod
    def roles_that_cannot_be_sent_invites_by_current_user(user_role):
        roles_not_allowed = {
            RedisUtil.get_role_id('OWNER'): 'OWNER',
        }
        if user_role != 'OWNER':
            roles_not_allowed[RedisUtil.get_role_id('ADMIN')] = 'ADMIN'
        return roles_not_allowed


@endpoint('/org/<string:org_id>/invitations/<string:invitation_id>/resend')
class ResendInvitation(BaseView):
    protected_methods = ['POST', 'GET']

    def post(self, user_data):
        pass


@endpoint('/org/<string:org_id>/invitations/accept')
class AcceptInvitation(BaseView):
    protected_methods = ['POST', 'GET']

    def post(self, user_data):
        pass
