from api.utils.constants import APP_EMAIL
from celery_config import celery_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import codecs


class EmailUtil:
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
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            return 'Failure'
        return 'Success'

    @staticmethod
    def send_mail_from_template(template_name, **kwargs):
        try:
            with codecs.open(
                    f'api/utils/emails/templates/{template_name}.html', 'r',
                    'utf-8') as f:
                text = f.readlines()
                for key, value in kwargs.items():
                    text = text.replace("{{" + key + '}}', value)

                return text
        except Exception:
            raise Exception('The template name you specified does not exist')
