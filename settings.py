from flask import Flask
from flask_restplus import Api
from flask_marshmallow import Marshmallow
import os
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import dotenv

db = SQLAlchemy()
dotenv.load_dotenv()
api_blueprint = Blueprint('api_bp', __name__, url_prefix='/api')
router = Api(api_blueprint)


class BaseConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('APP_SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_APP = 'app.py'


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


def create_app(current_env=os.getenv('ENVIRONMENT', 'production')):
    app = Flask(__name__)
    app.config.from_object(env_mapper[current_env])

    api = Api(app)

    ma = Marshmallow(app)
    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(api_blueprint)
    import api.views
    import api.models
    return app
