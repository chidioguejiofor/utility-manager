#!/usr/bin/env bash
echo "<<< API is now trying to connect to the database >>> "
echo "<<< Upgrade Database >>> "
flask db upgrade # upgrade db

sleep 2
echo "<<< Starting celery_config worker >>> "
exec celery -A  celery_config.celery_app worker --loglevel=info  & # runs celery_config worker

echo "<<< Feeling the beat by spinning up celery_config-beat >>> "
celery -A celery_config.celery_scheduler beat --loglevel=info  & #runs celery_config beat
sleep 5
echo "<<< Waiting for the celery_config-workers to flow with the beat >>> "
sleep 6
echo "Starting server >>> "

exec flask run -h  0.0.0.0 -p $PORT
