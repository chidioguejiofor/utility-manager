import json
import re
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors
from api.utils.constants import CONFIRM_TOKEN


def assert_send_grid_mock_send(mock_send,
                               receivers,
                               *,
                               num_of_calls=1,
                               bccs=None):
    bccs = bccs if bccs else []
    assert mock_send.called
    assert mock_send.call_count == num_of_calls
    if isinstance(receivers, str):
        receivers = [receivers]
    mail_obj = mock_send.call_args[0][0]
    personalization = mail_obj.personalizations[0]
    emails = [person['email'] for person in personalization.tos]
    assert emails == receivers
    if bccs:
        for email_obj in personalization.bccs:
            assert email_obj['email'] in bccs

    return mail_obj.contents[0].content


def assert_reg_confirm_email_was_sent_properly(html_content, redirect_url,
                                               user, token, link_id):
    # Extracting token from HTML content
    decoded = TokenValidator.decode_token(token, CONFIRM_TOKEN)
    decoded_data = decoded['data']

    confirm_email_endpoint = f'api/auth/confirm/{link_id}'
    # Validating token
    assert confirm_email_endpoint.format(token) in html_content
    assert decoded_data['email'] == user.email
    assert decoded_data['type'] == CONFIRM_TOKEN
    assert decoded_data['id'] == user.id
    assert decoded_data['redirect_url'] == redirect_url
    # checks that the expiry time of the token is 15 minutes
    assert decoded['exp'] - decoded['iat'] == 15 * 60


def assert_successful_response(response, message, status_code=200):
    response_body = json.loads(response.data)
    assert response.status_code == status_code
    assert response_body['message'] == message
    assert response_body['status'] == 'success'


def assert_when_token_is_missing(response):
    response_body = json.loads(response.data)
    assert response.status_code == 401
    assert response_body['message'] == authentication_errors['missing_token']
    assert response_body['status'] == 'error'


def assert_when_token_is_invalid(response):
    response_body = json.loads(response.data)
    assert response.status_code == 401
    assert response_body['message'] == authentication_errors['token_invalid']
    assert response_body['status'] == 'error'


def assert_paginator_meta(response_body, **kwargs):
    assert response_body['meta']['currentPage'] == kwargs['current_page']
    assert response_body['meta']['totalObjects'] == kwargs['total_objects']
    assert response_body['meta']['maxObjectsPerPage'] == kwargs[
        'max_objects_per_page']
    assert response_body['meta']['totalPages'] == kwargs['total_pages']
    assert response_body['meta']['nextPage'] == kwargs['next_page']
    assert response_body['meta']['previousPage'] == kwargs['prev_page']
    if kwargs['current_page'] > kwargs['total_pages']:
        assert len(response_body['data']) == 0
    elif kwargs['current_page'] == kwargs['total_pages']:
        assert len(response_body['data']) == kwargs['total_objects'] - (
            (kwargs['total_pages'] - 1) * kwargs['max_objects_per_page'])
    else:
        assert len(response_body['data']) == kwargs['max_objects_per_page']
