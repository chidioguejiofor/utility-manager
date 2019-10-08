import json

from api.utils.error_messages import authentication_errors


def assert_send_grid_mock_send(mock_send, receivers, *, num_of_calls=1):
    assert mock_send.called
    assert mock_send.call_count == num_of_calls
    if isinstance(receivers, str):
        receivers = [receivers]
    mail_obj = mock_send.call_args[0][0]
    personalization = mail_obj.personalizations[0]
    emails = [person['email'] for person in personalization.tos]
    assert emails == receivers


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
