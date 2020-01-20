from .base import BaseView, FilterByQueryMixin
from settings import endpoint
from flask import request
from api.schemas import InvitationRequestSchema, InvitationSchema
from api.models import Membership, Invitation, db
from api.utils.exceptions import ResponseException
from api.utils.success_messages import INVITING_USER_MSG_DICT, RETRIEVED
from api.utils.error_messages import invitation_errors, authentication_errors, serialization_error
from api.services.redis_util import RedisUtil
from sqlalchemy import exc, orm


@endpoint('/org/<string:org_id>/invitations')
class OrgInvitations(BaseView, FilterByQueryMixin):
    __model__ = Invitation
    protected_methods = ['POST', 'GET']
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

    def get(self, user_data, org_id):
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
                message=authentication_errors['forbidden'].format(
                    'access this'),
                status_code=403,
            )
        query_params = request.args
        query = self.search_model(query_params)
        query = query.options(
            orm.joinedload('role'), ).filter_by(organisation_id=org_id)
        page_query, meta = self.paginate_query(query, query_params)
        fields_to_exclude = [
            'role_id', 'user_dashboard_url', 'signup_url', 'organisation'
        ]
        data = InvitationSchema(many=True,
                                exclude=fields_to_exclude).dump_success_data(
                                    page_query,
                                    message=RETRIEVED.format('Invitations'))
        data['meta'] = meta
        return data, 200

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
                                    exclude=['role',
                                             'organisation']).dump(invitations)
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


@endpoint('/user/invitations')
class UserInvitationsView(BaseView, FilterByQueryMixin):
    __model__ = Invitation
    protected_methods = ['GET']
    SEARCH_FILTER_ARGS = {
        'role_id': {
            'filter_type': 'ilike'
        },
    }

    SORT_KWARGS = {'defaults': 'created_at', 'sort_fields': {'created_at'}}

    def get(self, user_data):
        query_params = request.args
        query = self.search_model(query_params)
        query = query.options(
            orm.joinedload('organisation'),
            orm.joinedload('role'),
        ).filter_by(email=user_data['email'], )
        page_query, meta = self.paginate_query(query, query_params)
        fields_to_exclude = ['role_id', 'user_dashboard_url', 'signup_url']
        data = InvitationSchema(many=True,
                                exclude=fields_to_exclude).dump_success_data(
                                    page_query,
                                    message=RETRIEVED.format('Invitations'))
        data['meta'] = meta
        return data, 200


@endpoint('/org/<string:org_id>/invitations/<string:invitation_id>/resend')
class ResendInvitation(BaseView):
    protected_methods = ['POST']

    def post(self, user_data):
        pass


@endpoint('/user/invitations/<string:invitation_id>/accept')
class AcceptInvitation(BaseView):
    protected_methods = ['POST']

    def post(self, user_data, invitation_id):
        pass
