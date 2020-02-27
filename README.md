[![CircleCI](https://circleci.com/gh/chidioguejiofor/utility-manager.svg?style=svg)](https://circleci.com/gh/chidioguejiofor/utility-manager)
# Utility Manager
This is a Utility Manager application that makes it easy for engineers to track the appliances in their
place of work. Some of the main  EPICs are:
- Engineer should be able to log the readings of parameters of an appliance to the app daily.
- Engineers should be able to create and export reports from the app.

## Setup App
Run the following commands:

- Ensure you have `Python 3.7.2`  installed from [here](https://www.python.org/downloads/release/python-372/)
- Install `pipenv` via: 
```bash
pip install pipenv
```
- Clone repo via:  
```bash
git clone https://github.com/chidioguejiofor/utility-manager.git
```
- Start virtual environment via:
```bash
pipenv shell
```
- Install dependencies via:
```bash
pipenv install
```
- Make bash scripts executable via:
```bash
chmod +x hooks/install_hooks.sh hooks/pre_commit.sh scripts/install_commit_template.sh
```
- Install hooks by running:
```bash
hooks/install_hooks.sh
```
- Install Git commit template by running:
```bash
scripts/install_commit_template.sh
```
- Use the `.env-sample` file to create a `.env` file with required environmental variables

## Linting Automation
The app is configured to automatically lint your files once you do a `git commit`. However you can decide to lint all 
python files by running 
```bash
yapf -ir $(find . -name '*.py')
``` 

Linting follows the [PE8 Style Guide](https://www.python.org/dev/peps/pep-0008/)

## Database and Migrations 
To setup the database simply follow these steps:
- Using your preferred tool, create the database and put the URL in the `DATABASE_URL` env variable
- Generate migrations from model by running

```bash
flask db migrate
```
- Upgrade your database by running:

```bash
flask db upgrade
```
- You should have your db setup properly.

Subsequently, if a new model is created or while rebasing data run the following to update your db:
- Generate migrations for new changes via:

```bash
flask db migrate
```
- Update your database via

```bash
flask db upgrade
```

## Starting the app
In order to start the app locally, run

```bash
flask run
``` 

## Documentation
You can all the endpoints in the postman documentation  here [![Open Docs](https://run.pstmn.io/button.svg)](https://documenter.getpostman.com/view/4208573/SVtVTT71)

## Redis and Celery
Celery is used as the message broker for the API. We use it to run heavy task(via celery-workers) and run cron-jobs(via celery-beat).

#### Starting Redis
In order to run celery, you would need to ensure that a `redis` is running. 
Using docker, you can achieve this by running 

```bash
docker run -p 6379:6379 redis
``` 
This would spin up a redis server in  port `6379` in your machine.

If your `redis server` is running on a different port/host, you must specify the URL in the `.env` file via key `REDIS_SERVER_URL`

#### Starting Celery
Once Redis is up and running, you can now spin up celery in these steps:

- Start celery worker by executing 

```bash
celery -A  celery_config.celery_app worker --loglevel=info
```
- In a separate terminal, spin up the celery beat via

```bash
celery -A  celery_config.celery_scheduler beat --loglevel=info
```

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
2. Execute the script via:

```bash
scripts/free_up_memory.sh
```

The above would free up memory that is used in your docker instance

## Running Tests
You can run tests for the app via: 

```bash
pytest --cov=api --cov-report=html
```

## Test Conventions
All features added to the app must fully tested with the aim being 95% coverage. 
Although the coverage is important, it more important to test the right things and necessary edge cases


## Seeding Infrastructure
In order to ensure data integrity we create a seeder infrastructure that would check that the data meets
certain requirements before it is seeded to the database. 

Everything related to seeders is in the seeders package. 

This infrastructure ensures that:
1. Data which are effectively the same is not seeded to the database twice
2. Unique constraints are met.
3. Trying to seed the same data more than once does not result in duplicate data
4. Seeded data can be easily viewed in YAML files.
5. Seeders can be generated either from list of dicts or a sqlachemy query object

### Generating Seed data

The steps to generating seed data to the db are as follows:

- Open the shell via

```bash
flask shell
```
- Create a list of dictionary or get a query object from the sqlachemy and store that in a variable
- Import seeders manager and call the `write_seed_data` function passing the required arguments

For example,
```python
from seeders.seeders_manager import SeederManager
roles = [

  {
    'name': 'admin',
    'description': 'The admin is second only to the owner of the organisation'
  },
   {
    'name': 'owner',
    'description': 'This represents the owner of the organisation'
  },
  {
    'name': 'engineer',
    'description': 'An engineer should be allowed to do things like logging but should not be able to invite users to the organistion'
  },
  {
    'name': 'regular users',
    'description': 'This represents non engineering members of the organisation'
  }
]

SeederManager.write_seed_data('role', roles) # generates fixtures in seeders/fixture

```
The above is exactly how the roles seed data was generated. Note that you would need to configure SeedManager 
to recognise the 'key' (which is 'role' in this case)  and the steps for that is shown in the next 2 sub-section.

### Seeding the database

Once you have generated the data to be seeded open the shell and run: 

```bash
flask seed [key]
```

The command takes an optional `key` argument that specifies the exact table to seed. If the key
is not provided then all the seeders that have been configured are run


### Adding new Seeders to the app
When a model requires a seeder, it should be created
in model_seeders module, extend `BaseSeeder` and override the following methods:

- `__eq__`: This would be used to determine when two seeders are equal to each other
- `model_filter`: This returns a `sqlalchemy.sql.elements.BinaryExpression`
(created by comparing a model attribute eg. `User.first_name == 'ada'` ) that determines how the seeder object
would be compared with the model to ensure that it has not already been created.
- `to_dict`: should return a dictionary that with the model attributes key-value pairs.

For example, assuming we have seeders for users( we don't!). It would look something like this

```python

from seeders.model_seeders.base import BaseSeeder
from api.models import User as UserModel
from api.utils.id_generator import IDGenerator

class UserSeed(BaseSeeder):
    __model__ = UserModel
    KEY = 'user'

    def __init__(self,
                 first_name,
                 last_name,
                 username,
                 email,
                **kwargs):
        super().__init__(**kwargs)
        self.id = id if id else IDGenerator.generate_id()
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email

    def __eq__(self, other):
        return self.username == other.username or self.email == other.email

    def model_filter(self):
        return (
                (self.__model__.username == self.username)  | (self.__model__.email == self.email)
        )
    
    def __lt__(self, other):
        return False

    def __repr__(self):
        return "%s(username=%r,first_name=%r, last_name=%r, email=%r, created_at=%s, updated_at=%s)" % (
            self.__class__.__name__,
            self.username,
            self.first_name,
            self.last_name,
            self.email,
            self.created_at,
            self.updated_at,
        )

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

```

Once you have done this, the next thing is to make the `SeederManager` 'aware' of the new seeder by adding it to 
the `MAPPER` dictionary. With that you are done. 


