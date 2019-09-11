# Get Base image
FROM python:3.7.2

MAINTAINER Prof<chidioguejiofor@gmail.com>

# Install pipenv using pip
RUN pip install pipenv

# Make /api the working directory
WORKDIR /api-data

# Copy ./Pipfile and ./Pipfile.lock to the working directory
COPY ./Pipfile /api-data
COPY ./Pipfile.lock /api-data

# Install dependencies in the Pipfile
RUN  pipenv install --system  --deploy --ignore-pipfile

# Copy all the other files/folders to api
COPY . /api-data

# Make the scripts/entrypoint.sh bash script
ADD  docker-dev/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create non-super user. This user would be used to run celery_config later on
RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser celery_user

USER root

# Expose port 7000 to the world
EXPOSE 7000

# Start app by running entrypoint.sh bash script
ENTRYPOINT ["entrypoint.sh"]
