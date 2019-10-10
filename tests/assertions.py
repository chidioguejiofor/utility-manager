import json
import re
from api.utils.token_validator import TokenValidator
from api.utils.error_messages import authentication_errors
from api.utils.constants import CONFIRM_TOKEN


def assert_send_grid_mock_send(mock_send, receivers, *, num_of_calls=1):
    assert mock_send.called
    assert mock_send.call_count == num_of_calls
    if isinstance(receivers, str):
        receivers = [receivers]
    mail_obj = mock_send.call_args[0][0]
    personalization = mail_obj.personalizations[0]
    emails = [person['email'] for person in personalization.tos]
    assert emails == receivers
    return mail_obj.contents[0].content


def assert_reg_confirm_email_was_sent_properly(html_content, redirect_url,
                                               user):
    # Extracting token from HTML content
    token_pattern = r"\/e.+\.e.+\..+\""
    token = re.findall(token_pattern, html_content)[0][1:-1]
    decoded = TokenValidator.decode_token(token, CONFIRM_TOKEN)
    decoded_data = decoded['data']

    confirm_email_endpoint = 'api/auth/confirm/{}'
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
