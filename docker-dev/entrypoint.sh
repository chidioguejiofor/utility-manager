#!/usr/bin/env bash

echo "<<< API is sleeping for 30 seconds to allow Database to connect >>> "
sleep 30 # waiting for the postgres db and redis to start up first
mkdir -p dumped_files
echo "<<< API is now trying to connect to the database >>> "
echo "<<< Upgrade Database >>> "
flask db upgrade # migrate db
flask seed

sleep 6
echo "<<< Starting celery_config worker >>> "
exec celery -A  celery_config.celery_app worker --loglevel=info --uid=celery_user & # runs celery_config worker

echo "<<< Feeling the beat by spinning up celery_config-beat >>> "
celery -A celery_config.celery_schedules beat --loglevel=info --uid=celery_user & #runs celery_config beat
sleep 5
echo "<<< Waiting for the celery_config-workers to flow with the beat >>> "

echo "Starting server >>> "
exec flask run -p 7000


