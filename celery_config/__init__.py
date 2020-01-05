from settings import make_celery, create_app

app = create_app()

celery_app = make_celery(app)
