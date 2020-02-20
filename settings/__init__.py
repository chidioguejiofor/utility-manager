from flask import Flask
from flask_restplus import Api
import os
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import dotenv
import inspect
from .configs import ENV_MAPPER
from .service_config import add_id_event_to_models, create_cli_commands
from .error_handlers import create_error_handlers
db = SQLAlchemy()
dotenv.load_dotenv()
api_blueprint = Blueprint('api_bp', __name__, url_prefix='/api')
org_blueprint = Blueprint('org_bp',
                          __name__,
                          url_prefix='/api/org/<string:org_id>')
bp = Blueprint('errors', __name__)
router = Api(api_blueprint)
org_router = Api(org_blueprint)
endpoint = router.route
org_endpoint = org_router.route


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
    app.config.from_object(ENV_MAPPER[current_env])
    api = Api(app)
    db.init_app(app)
    migrate = Migrate(app, db)

    app.register_blueprint(api_blueprint)
    app.register_blueprint(bp)
    app.register_blueprint(org_blueprint)
    import api.views
    import api.models as models
    tables_in_my_app = [
        cls for cls in db.Model._decl_class_registry.values()
        if isinstance(cls, type) and issubclass(cls, db.Model)
    ]
    add_id_event_to_models(tables_in_my_app)

    create_error_handlers(app)
    create_cli_commands(app)

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
