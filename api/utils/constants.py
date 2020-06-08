"""Add constants used in the app to this file"""
CELERY_TASKS = ['api.services.file_uploader', 'api.utils.emails']
APP_EMAIL = 'info@utility-manager.com'
CONFIRM_EMAIL_SUBJECT = 'Complete Registration'
RESET_PASSWORD_SUBJECT = 'Reset Password'
CONFIRM_TOKEN = 0
LOGIN_TOKEN = 1
RESET_TOKEN = 2
FAILED_LOGIN_LIMITS = 6
COOKIE_TOKEN_KEY = 'T_KEY'
REDIS_TOKEN_HASH_KEY = 'TOKEN'
SENTRY_IGNORE_ERRORS = [
    'api.utils.exceptions.UniqueConstraintException',
    'api.utils.exceptions.ResponseException',
    'api.utils.exceptions.ModelOperationException',
    'marshmallow.exceptions.ValidationError',
    'jwt.exceptions.InvalidTokenError',
]
GENERIC_EXCLUDE_SCHEMA_FIELDS = ['created_at', 'updated_at']
GENERIC_EXCLUDE_USER_AUDIT_FIELDS = GENERIC_EXCLUDE_SCHEMA_FIELDS + [
    'created_by', 'updated_by'
]
EXCLUDE_USER_SCHEMA_FIELDS = GENERIC_EXCLUDE_SCHEMA_FIELDS + ['verified']
ID_FIELD_LENGTH = 21
