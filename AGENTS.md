# Overview
A tutorial project, which focuses on use cases on using Celery tasks within a Django Rest Framework application.

Current plan, key architecture decisions and other ideas related to the project are stored in `docs/to-do.md`.


## Project Stack
- Python 3.13;
- DRF as a web-framework;
- PostgreSQL as a database (SQLite as a stub on start);
- Celery as a task runner;
- RabbitMQ as Celery's message broker;
- Docker Compose for running project's development and test environment;
- python-dotenv;
- pytest-django for tests;


## Key Project Goals
- define basic project layout & infrastructure;
- implement speicif scenarios, where Celery is used for running async tasks triggered by DRF request processing:
    - "send" an activation email when a user registers:
        - process request -> trigger email "sending" task -> process task;
        - ensure idempotency and proper failure processing on all stages of the task;
    - potentially, other scenarios later on.


## Project Layout
- `docs` - project to-do list & documentation;
- `src` - project source code:
    `api` - root app;
    `users`:
        - override of auth.user;
        - used in the "send" email task;
- `tests` - project tests:
    - `tests`:
        - subdirectory with test case files;
        - has nested subdirectories for tests of different types (`migrations`, `views`, `tasks`);
        - test case location in nested subdirectories should follow the structure of `src` dir;