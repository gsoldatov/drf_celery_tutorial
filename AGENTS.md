# Overview
A tutorial project, which focuses on use cases for Celery tasks within a Django Rest Framework application.

Current plan, key architecture decisions and other ideas related to the project are stored in `docs/to-do.md`.


## Project Stack
- Python 3.13;
- DRF as a web-framework;
- PostgreSQL 17 as a database;
- Celery as a task runner;
- Celery Beat + shelve for periodic tasks;
- RabbitMQ as Celery's message broker;
- Docker Compose for running project's development and test environment;
- pytest-django for tests;


## Key Project Goals
- define basic project layout & infrastructure;
- implement scenarios, where Celery is used for running async tasks triggered by DRF request processing:
    - "send" a verification email when a user registers:
        - process request -> trigger email "sending" task -> process task;
        - ensure idempotency and proper failure processing on all stages of the task;
    - periodically clear expired email verification token;
    - potentially, other scenarios later on.


## Project Layout
- `docs` - project to-do list & documentation;
- `src` - project source code:
    `api`:
        - root app;
        - stores project and Celery configurations;
    `users`:
        - override of auth.user;
        - used in the "send" verification email and verification tokens cleanup task;
        - contains several endpoints and Celery tasks;
- `tests` - project tests:
    - `tests`:
        - subdirectory with test case files;
        - has nested subdirectories for tests of different types:
            - `config` - tests .env file validation;
            - `migrations` - tests if database migrations work properly;
            - `serializers` - tests request validation logic of serializers (but not DB interactions);
            - `views`:
                - tests view logic and database interactions;
                - mocks Celery tasks with pytest-mock;
            - `tasks`
                - tests Celery tasks lifecycle, idempotency, error processing, etc.;
        - test case location in nested subdirectories should follow the structure of `src` dir;


## Test Writing Guidelines
- View tests are performed using a test db in PostgreSQL container (standard pytest-django approach);
- task tests are performed using PostgreSQL and RabbitMQ containers (like for DB, a single test queue is created for a test module and purged after a test);
- network errors are simulated by changing app configuration with a fixture on inside a test case (e.g., by changing port of a service);
- Celery Beat tests:
    - are permormed using containers as well, where applicable;
    - periodic tasks can be invoked directly, instead of adding separate fixtures for triggering beats;