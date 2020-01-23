"""Add constants used in the app to this file"""
CELERY_TASKS = ['api.services.file_uploader', 'api.utils.emails']
APP_EMAIL = 'info@utility-manager.com'
CONFIRM_EMAIL_SUBJECT = 'Complete Registration'
RESET_PASSWORD_SUBJECT = 'Reset Password'
CONFIRM_TOKEN = 0
LOGIN_TOKEN = 1
RESET_TOKEN = 2
SENTRY_IGNORE_ERRORS = [
    'api.utils.exceptions.UniqueConstraintException',
    'api.utils.exceptions.ResponseException',
    'api.utils.exceptions.ModelOperationException',
]