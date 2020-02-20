from .base import BaseView, BasePaginatedView, BaseOrgView
from settings import org_endpoint, endpoint
from flask import request
from api.schemas import (InvitationRequestSchema, InvitationSchema,
                         MembershipIDOnlySchema,
                         InvitationRequestWithoutInvitesSchema)
from api.models import Membership, Invitation, User
from api.utils.exceptions import ResponseException
from api.utils.success_messages import INVITING_USER_MSG_DICT, RETRIEVED, ADDED_TO_ORG
from api.utils.error_messages import invitation_errors, serialization_error
from api.services.redis_util import RedisUtil


@org_endpoint('/invitations')
class OrgInvitations(BaseOrgView, BasePaginatedView):
    __model__ = Invitation
    # auth_settings
    protected_methods = ['POST', 'GET']

    # query settings
    SEARCH_FILTER_ARGS = {
        'role_id': {
            'filter_type': 'ilike'
        },
        'email': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {
        'defaults': 'created_at',
        'sort_fields': {'created_at', 'role_id'}
    }

    __SCHEMA__ = InvitationSchema
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Invitations')
    SCHEMA_EXCLUDE = [
        'role_id', 'user_dashboard_url', 'signup_url', 'organisation'
    ]
    EAGER_LOADING_FIELDS = ['role']

    # org view settings
    ALLOWED_ROLES = {
        'GET': ['OWNER', 'ADMIN'],
        'POST': ['OWNER', 'ADMIN'],
    }

    def post(self, user_data, org_id, membership):
        request_data = request.get_json()
        list_of_existing_emails, list_of_models = self.extract_inv_model_list(
            membership, org_id)
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
                                    exclude=['role',
                                             'organisation']).dump(invitations)
        return self.generate_response(list_of_existing_emails, list_of_models,
                                      res_data)

    def extract_inv_model_list(self, membership, org_id):
        request_data = request.get_json()
        roles_user_cannot_send_invites = self.roles_that_cannot_be_sent_invites_by_current_user(
            membership.role.name)

        invitations = InvitationRequestSchema(
            roles_user_cannot_send_invites=roles_user_cannot_send_invites,
        ).load(request_data)

        email_inputs = [invitation['email'] for invitation in invitations]
        existing_emails = Invitation.query.filter(
            Invitation.email.in_(email_inputs)).all()
        already_memberships = Membership.eager('member').filter(
            Membership.organisation_id == org_id).join(User).filter(
                User.email.in_(email_inputs)).all()
        already_member_emails = set(mship.member.email
                                    for mship in already_memberships)
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
            elif inv['email'] in already_member_emails:
                list_of_existing_emails.append({
                    'email':
                    inv['email'],
                    'message':
                    invitation_errors['email_already_in_org']
                })
            else:
                list_of_models.append(Invitation(**inv,
                                                 organisation_id=org_id))
        return list_of_existing_emails, list_of_models

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


@org_endpoint('/invitations/<string:invitation_id>/resend')
class ResendInvitation(BaseOrgView):
    protected_methods = ['POST']
    # org view settings
    ALLOWED_ROLES = {
        'POST': ['OWNER', 'ADMIN'],
    }

    def post(self, user_data, invitation_id, org_id, membership):
        invitation = Invitation.query.filter_by(
            id=invitation_id,
            organisation_id=org_id,
        ).first()

        if not invitation:
            raise ResponseException(
                message=serialization_error['not_found'].format('Invitation'),
                status_code=404,
            )

        invitation_requests = InvitationRequestWithoutInvitesSchema().load(
            request.get_json())

        Invitation.send_email_to_users(
            dashboard_url=invitation_requests['user_dashboard_url'],
            signup_url=invitation_requests['signup_url'],
            inviter_membership=membership,
            emails=[invitation.email])

        return {'status': 'success', 'message': 'Invitation was re-sent.'}, 202


@endpoint('/user/invitations')
class UserInvitationsView(BaseView, BasePaginatedView):
    __model__ = Invitation
    protected_methods = ['GET']
    SEARCH_FILTER_ARGS = {
        'role_id': {
            'filter_type': 'eq'
        },
        'role.name': {
            'filter_type': 'ilike'
        },
    }
    __SCHEMA__ = InvitationSchema
    EAGER_LOADING_FIELDS = ['organisation', 'role']
    SORT_KWARGS = {
        'defaults': 'created_at',
        'sort_fields': {'created_at', 'role.name'}
    }
    RETRIEVE_SUCCESS_MSG = RETRIEVED.format('Invitations')
    SCHEMA_EXCLUDE = ['role_id', 'user_dashboard_url', 'signup_url']

    def filter_get_method_query(self, query, **kwargs):
        user_data = kwargs.get('user_data')
        return query.filter(Invitation.email == user_data['email'])


@endpoint('/user/invitations/<string:invitation_id>/accept')
class AcceptInvitation(BaseView):
    protected_methods = ['POST']

    def post(self, user_data, invitation_id):

        invitation = Invitation.eager('role', 'organisation').filter_by(
            email=user_data['email'],
            id=invitation_id,
        ).first()
        if invitation is None:
            raise ResponseException(
                message=serialization_error['not_found'].format('Invitation'),
                status_code=404,
            )
        membersip = Membership(
            user_id=user_data['id'],
            role_id=invitation.role.id,
            organisation_id=invitation.organisation_id,
        )
        membersip.save(commit=False)
        final_response = MembershipIDOnlySchema(
            exclude=['user_id']).dump_success_data(membersip, ADDED_TO_ORG)
        invitation.delete(commit=True)
        return final_response, 201
