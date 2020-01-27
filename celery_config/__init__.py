from settings.service_config import make_celery
from settings import create_app

app = create_app()

celery_app = make_celery(app)
