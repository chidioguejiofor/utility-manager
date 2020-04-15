#!/usr/bin/env bash
echo "<<< API is now trying to connect to the database >>> "
mkdir -p dumped_files
echo "<<< Upgrade Database >>> "
flask db upgrade # upgrade db
flask seed
sleep 2
echo "<<< Starting celery_config worker >>> "
celery -A  celery_config.celery_app worker --loglevel=info --detach   # runs celery_config worker
##
#echo "<<< Feeling the beat by spinning up celery_config-beat >>> "
#celery -A celery_config.celery_scheduler beat --loglevel=info  & #runs celery_config beat
#sleep 5
#echo "<<< Waiting for the celery_config-workers to flow with the beat >>> "
sleep 6
echo "Starting server >>> "

exec gunicorn --bind 0.0.0.0:$PORT  wsgi:app
