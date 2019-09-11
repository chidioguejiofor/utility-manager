from celery import Celery
from api.utils.constants import CELERY_TASKS
from app import app
import os
import dotenv
dotenv.load_dotenv()

REDIS_SERVER_URL = os.getenv('REDIS_SERVER_URL', 'redis://localhost')
celery_app = Celery(app.name, broker=REDIS_SERVER_URL, include=CELERY_TASKS)
celery_app.conf.update(app.config)
celery_scheduler = Celery(app.name, broker=REDIS_SERVER_URL)
celery_scheduler.conf.update(app.config)
celery_scheduler.conf.enable_utc = False
