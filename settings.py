from flask import Flask
from flask_restplus import Api
from sqlalchemy import event
from api.utils.time_util import TimeUtil
from api.utils.error_messages import serialization_error
from api.utils.exceptions import UniqueConstraintException
import os
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow.exceptions import ValidationError
import dotenv

db = SQLAlchemy()
dotenv.load_dotenv()
api_blueprint = Blueprint('api_bp', __name__, url_prefix='/api')
bp = Blueprint('errors', __name__)
router = Api(api_blueprint)


class BaseConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('APP_SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_APP = 'app.py'
    CELERY_BROKER_URL = os.getenv('REDIS_SERVER_URL')


class ProductionConfig(BaseConfig):
    TESTING = False
    FLASK_ENV = 'production'


class StagingConfig(BaseConfig):
    pass


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
    from api.models.base.id_generator import IDGenerator

    for table in tables_in_my_app:
        event.listen(table, 'before_insert',
                     IDGenerator.generate_id_before_insert)
        event.listen(table, 'before_update',
                     TimeUtil.generate_time_before_update)


def create_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_errors(error):
        return {
            'errors': error.messages,
            'status': 'error',
            'message': serialization_error['invalid_field_data']
        }, 400

    @app.errorhandler(UniqueConstraintException)
    def handle_unique_errors(error):
        return {'status': 'error', 'message': error.message}, 409


def create_app(current_env=os.getenv('ENVIRONMENT', 'production')):
    app = Flask(__name__)
    app.config.from_object(env_mapper[current_env])

    api = Api(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(api_blueprint)
    app.register_blueprint(bp)
    import api.views
    import api.models
    tables_in_my_app = [
        cls for cls in db.Model._decl_class_registry.values()
        if isinstance(cls, type) and issubclass(cls, db.Model)
    ]
    add_id_event_to_models(tables_in_my_app)

    create_error_handlers(app)

    return app
