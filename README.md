[![CircleCI](https://circleci.com/gh/chidioguejiofor/utility-manager.svg?style=svg)](https://circleci.com/gh/chidioguejiofor/utility-manager)
# Utility Manager
This is a Utility Manager application that makes it easy for engineers to track the appliances in their
place of work. Some of the main  EPICs are:
- Engineer should be able to log the readings of parameters of an appliance to the app daily.
- Engineers should be able to create and export reports from the app.

## Setup App
Run the following commands:

- Ensure you have `Python 3.7.2`  installed from [here](https://www.python.org/downloads/release/python-372/)
- Install `pipenv` via `pip install pipenv`
- Clone repo via  `git clone https://github.com/chidioguejiofor/utility-manager.git`
- Start virtual environment via `pipenv shell`
- Install dependencies via `pipenv install`
- Make bash scripts executable via: ` chmod +x hooks/install_hooks.sh hooks/pre_commit.sh scripts/install_commit_template.sh`
- Install hooks by running: `hooks/install_hooks.sh`
- Install Git commit template by running: `scripts/install_commit_template.sh`
- Use the `.env-sample` file to create a `.env` file with required environmental variables

## Linting Automation
The app is configured to automatically lint your files once you do a `git commit`. However you can decide to lint all 
python files by running `yapf -ir $(find . -name '*.py')`. 
Linting follows the [PE8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

## Database and Migrations 
To setup the database simply follow these steps:
- Using your preferred tool, create the database and put the URL in the `DATABASE_URL` env variable
- Generate migrations from model by running `flask db migrate`
- Upgrade your database by running: `flask db upgrade`
- You should have your db setup properly.

Subsequently, if a new model is created or while rebasing data run the following to update your db:
- Generate migrations for new changes via: `flask db migrate`
- Update your database via `flask db upgrade`

## Starting the app
In order to start the app locally, run `flask run`. 

## Documentation
You can all the endpoints in the postman documentation  here [![Open Docs](https://run.pstmn.io/button.svg)](https://idonthaveone.postman.co/collections/4208573-b19f1723-afe4-4752-b51c-0ea93cf6b495/publish?workspace=2a395d64-1d2c-41cc-ab03-6014fdfd989f)

## Redis and Celery
Celery is used as the message broker for the API. We use it to run heavy task(via celery-workers) and run cron-jobs(via celery-beat).

#### Starting Redis
In order to run celery, you would need to ensure that a `redis` is running. 
Using docker, you can achieve this by running `docker run -p 6379:6379 redis`. This would spin up a redis server in  port `6379` in your machine.

If your `redis server` is running on a different port/host, you must specify the URL in the `.env` file via key `REDIS_SERVER_URL`

#### Starting Celery
Once Redis is up and running, you can now spin up celery in these steps:

- Start celery worker by executing  `celery -A  celery_config.celery_app worker --loglevel=info`
- In a separate terminal, spin up the celery beat via `celery -A  celery_config.celery_scheduler beat --loglevel=info`

## Docker Setup
You could also easily start the API, Celery and Redis by using docker in the following steps:

1. Download and Install Docker from [Docker Getting Started Page](https://www.docker.com/get-started)
2. Ensure that Docker is installed by running `docker --version`. This should display the version of docker on your machine
3. In Project directory, use _docker-compose_ to build the app  by running  `docker-compose build`.
4. Start the app via `docker-compose up`. You could add the `-d`(`docker-compose -d`) if you don't want to see the logs of the app.
5. Run` docker ps` to see that the airtech app is running
6. You should be able to connect to the app via the `localhost`

When you are done running your app with docker, it is best to free up resources that is used. To do this follow these steps:

1. Make the *free_up_memory.sh* bash script executable by running `chmod +x scripts/free_up_memory.sh`
2. Execute the script via: `scripts/free_up_memory.sh`

The above would free up memory that is used in your docker instance

## Running Tests
You can run tests for the app via: `pytest --cov=api --cov-report=html`

## Test Conventions
All features added to the app must fully tested with the aim being 95% coverage. 
Although the coverage is important, it more important to test the right things and necessary edge cases

