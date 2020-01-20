from flask import Flask
from flask_restplus import Api
from sqlalchemy import event
from api.utils.time_util import TimeUtil
from api.utils.error_messages import serialization_error, authentication_errors
from api.utils.exceptions import UniqueConstraintException, ResponseException, ModelOperationException
from api.utils.constants import CELERY_TASKS
import os
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow.exceptions import ValidationError
from flask_cors import CORS
import dotenv
import logging
from celery import Celery, Task
from jwt.exceptions import PyJWTError, ExpiredSignature
import werkzeug.exceptions
import cloudinary
import inspect

db = SQLAlchemy()
dotenv.load_dotenv()
api_blueprint = Blueprint('api_bp', __name__, url_prefix='/api')
bp = Blueprint('errors', __name__)
router = Api(api_blueprint)
endpoint = router.route

cloudinary.config(cloud_name=os.getenv('CLOUDINARY_NAME'),
                  api_key=os.getenv('CLOUDINARY_API_KEY'),
                  api_secret=os.getenv('CLOUDINARY_SECRET'))

REDIS_SERVER_URL = os.getenv('REDIS_SERVER_URL', 'redis://localhost')
celery_scheduler = Celery(__name__, broker=REDIS_SERVER_URL)
celery_scheduler.conf.enable_utc = False


class BaseConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('APP_SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_APP = 'app.py'
    CELERY_BROKER_URL = os.getenv('REDIS_SERVER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND',
                                      default='redis://localhost:6379/0')


class ProductionConfig(BaseConfig):
    TESTING = False
    FLASK_ENV = 'production'
    PROPAGATE_EXCEPTIONS = True


class StagingConfig(BaseConfig):
    TESTING = False
    PROPAGATE_EXCEPTIONS = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL')


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = 'development'


env_mapper = {
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'development': DevelopmentConfig,
}


def add_id_event_to_models(tables_in_my_app):
    # The table retrival code was gotten from stack-overflow in
    # https://stackoverflow.com/questions/26514823/get-all-models-from-flask-sqlalchemy-db

    for table in tables_in_my_app:
        event.listen(table, 'before_update',
                     TimeUtil.generate_time_before_update)


def create_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_errors(error):
        if '_schema' in error.messages:
            error.messages = error.messages['_schema']
        return {
            'status': 'error',
            'errors': error.messages,
            'message': serialization_error['invalid_field_data']
        }, 400

    @app.errorhandler(ResponseException)
    def handle_errors(error):
        error_dict = {
            'status': 'error',
            'message': error.message,
        }

        if error.errors:
            error_dict['errors'] = error.errors

        return error_dict, error.status_code

    @app.errorhandler(ModelOperationException)
    def handle_errors(error):
        return {
            'status': 'error',
            'message': error.api_message,
        }, error.status_code

    @app.errorhandler(PyJWTError)
    def handle_errors(error):
        if isinstance(error, ExpiredSignature):
            return {
                'status': 'error',
                'message': authentication_errors['session_expired'],
            }, 401
        else:
            return {
                'status': 'error',
                'message': authentication_errors['token_invalid'],
            }, 401

    @app.errorhandler(UniqueConstraintException)
    def handle_unique_errors(error):
        return {'status': 'error', 'message': error.message}, 409

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def handle_resource_not_found(error):
        return {'status': 'error', 'message': 'Resource was not found'}, 404

    @app.errorhandler(Exception)
    def handle_any_other_errors(error):
        logging.exception(error)
        return {'status': 'error', 'message': 'Unknown Error'}, 500


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


def create_app(current_env=os.getenv('FLASK_ENV', 'production')):
    app = Flask(__name__)
    origins = ['*']
    if current_env == 'production':
        origins = ['https://utility-manager-frontend.herokuapp.com']

    if current_env == 'development':
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    CORS(app, origins=origins, supports_credentials=True)
    app.config.from_object(env_mapper[current_env])
    api = Api(app)
    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(api_blueprint)
    app.register_blueprint(bp)
    import api.views
    import api.models as models
    tables_in_my_app = [
        cls for cls in db.Model._decl_class_registry.values()
        if isinstance(cls, type) and issubclass(cls, db.Model)
    ]
    add_id_event_to_models(tables_in_my_app)

    create_error_handlers(app)
    # celery_scheduler.conf.update(app.config)

    @app.shell_context_processor
    def make_shell_context():
        import api.schemas as schemas
        object_dicts = {
            model_name: model_obj
            for model_name, model_obj in inspect.getmembers(
                models, inspect.isclass)
        }
        for schema_name, schema_obj in inspect.getmembers(
                models, inspect.isclass):
            object_dicts[schema_name] = schema_obj
        return object_dicts

    return app
