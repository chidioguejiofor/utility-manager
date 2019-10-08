from api.utils.constants import APP_EMAIL
from celery_config import celery_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import codecs
import logging
from flask import request
from api.utils.token_validator import TokenValidator
from api.utils.constants import CONFIRM_TOKEN, CONFIRM_EMAIL_SUBJECT


class EmailUtil:
    SEND_CLIENT = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

    @staticmethod
    @celery_app.task(name='send-email-to-user-as-html')
    def send_mail_as_html(subject, receivers, html):
        """Sends mail as html

        Args:
            subject(str): The subject of the email
            receivers(list):  A list of emails of the receivers
            html(str): The html to be sent as a mail

        Returns:
            (str): Returns 'success' if the mail is sent successfully
        """

        message = Mail(from_email=APP_EMAIL,
                       to_emails=receivers,
                       subject=subject,
                       html_content=html)
        try:

            response = EmailUtil.SEND_CLIENT.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            logging.exception(e)
            return 'Failure'
        return 'Success'

    @classmethod
    def send_confirmation_email(cls, user):

        token = TokenValidator.create_token({
            'type': CONFIRM_TOKEN,
            'id': user.id,
            'email': user.email,
            'redirect_url': user.redirect_url
        })
        confirm_link = f'{request.host_url}api/auth/confirm/{token}'
        html = cls.extract_html_from_template('confirm-email',
                                              confirm_link=confirm_link)
        cls.send_mail_as_html.delay(CONFIRM_EMAIL_SUBJECT, user.email, html)

    @staticmethod
    def extract_html_from_template(template_name, **kwargs):
        """Extracts HTML text from template file

        Reads the HTML file, replaces the arguments with the value in kwargs and
        Returns the resulting html as string

        Args:
            template_name: The name of a file in api/utils/emails/templates
            **kwargs:

        Returns:
            (str): The HTML that was read and parsed from the template file

        """
        with codecs.open(f'api/utils/emails/templates/{template_name}.html',
                         'r', 'utf-8') as f:
            text = ''.join(f.readlines())

            for key, value in kwargs.items():
                text = text.replace("{{" + key + '}}', value)
            print(text)
            return text
