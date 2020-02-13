import dotenv
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

import os
import click
from sqlalchemy import event
import cloudinary
from api.utils.time_util import TimeUtil
from api.utils.constants import CELERY_TASKS, SENTRY_IGNORE_ERRORS
from celery import Celery
dotenv.load_dotenv()

REDIS_SERVER_URL = os.getenv('REDIS_SERVER_URL', 'redis://localhost')
celery_scheduler = Celery(__name__, broker=REDIS_SERVER_URL)
celery_scheduler.conf.enable_utc = False
cloudinary.config(cloud_name=os.getenv('CLOUDINARY_NAME'),
                  api_key=os.getenv('CLOUDINARY_API_KEY'),
                  api_secret=os.getenv('CLOUDINARY_SECRET'))


def add_id_event_to_models(tables_in_my_app):
    # The table retrival code was gotten from stack-overflow in
    # https://stackoverflow.com/questions/26514823/get-all-models-from-flask-sqlalchemy-db

    for table in tables_in_my_app:
        event.listen(table, 'before_update',
                     TimeUtil.generate_time_before_update)


def make_celery(app):
    celery = Celery(app.import_name,
                    backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASKS)
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    if os.getenv('FLASK_ENV', 'development') != 'testing':
        celery.Task = ContextTask
    return celery


def create_cli_commands(app):
    @app.cli.command('seed')
    @click.argument('key', required=False)
    def seed(key=None):
        from seeders.seeders_manager import SeederManager
        SeederManager.run(key)


flask_env = os.getenv('FLASK_ENV')
if flask_env in ['production', 'staging']:
    sentry_sdk.init(dsn=os.getenv('SENTRY_IO_URL'),
                    integrations=[FlaskIntegration()],
                    ignore_errors=SENTRY_IGNORE_ERRORS,
                    environment=flask_env)
    sentry_sdk.init(os.getenv('SENTRY_IO_URL'),
                    integrations=[CeleryIntegration()])
