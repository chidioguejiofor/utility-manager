"""Add constants used in the app to this file"""
CELERY_TASKS = ['api.utils.emails']
APP_EMAIL = 'utility-manager@email.com'
CONFIRM_EMAIL_SUBJECT = 'Complete Registration'
RESET_PASSWORD_SUBJECT = 'Reset Password'
CONFIRM_TOKEN = 0
LOGIN_TOKEN = 1
RESET_TOKEN = 2
