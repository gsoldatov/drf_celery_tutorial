# Implementation Plan
+ plan architecture;
+ drf:
    + set up project:
        + venv, dependencies & django initialization;
        + .env file config -> loading & validation;
    + set up orm schemas & db migrations:
        + user:
            + override default auth user;
            + fields (use exact or similar AbstractUser fields where possible): id, first_name, last_name, email, email_verified (bool, false until email is verified);
        + email_verification_tokens (id, user_id, token, expires_at);
    + set up route handlers without celery:
        + user registration (validate -> add a user to the database -> register a task on commit (later, when celery is added));
        + get an existing user;
        + verify user email (get token from URL -> check if it exists -> change email_verified of a corresponding user);
    + add docker-compose.yml:
        x drf;          // opted to run dev server & tests locally
        + postgresql;
    + add tests:
        + use pytest;
        + fixtures:
            x test db setup & teardown; // once per test file       // using standard pytest-django db instead
            x test db cleanup;  // truncate after each test
            + test client;
        + test cases:
            + migrations;
            + serializers (validation);
            + views:
                + add a Celery task stub in view, but make it mockable for isolated testing of views;
    
    + validate .env file, when loading:
        + add validation tests;
    + rename artifacts related to email_verified field to match its name;

- configure celery:
    + add rabbitmq to docker-compose.yml;
    + update prjoect config -> configure celery & rabbitmq;
    - add email task:
        - add a task function;
        - ensure task idempotency;
        - configure task retries;
        - configure at least once delivery;

    x add a worker to docker-compose.yml;   // local process is used instead

    - add integration tests for celery tasks:
        - update fixtures:
            - test rabbitmq queue setup & teardown;
            ? other;
        - test cases:
            - integration cases for tasks:
                - successful task;
                - idempotency;
                - failure & retry:
                    - operational errors:
                        - broker or DB down);
                    ? application errors (figure out edge cases)
                    ? monkeypatch task or a function called inside it to simulate failures
            - integration test cases for views:
                - db down;
                - broker down;

- more test cases:
    - views -> db down;

- add admin user & test the full setup manually;
? add admin user to config;
? add a script / functions for setting up dev environment (running migrations, etc.);
- add readme;


# Key Architecture Decisions
## App & Celery General
- views with multiple database operations should wrap them in a single transaction;
- no auth restrictions for views;
- Celery tasks are dispatched via `transaction.on_commit()`;

## Celery Cases
### Email "Sending" Task
    - working with an override of auth.user model;
    - `email_verification_tokens` table stored email validation tokens;
    - not using django-celery-results, since it's redundant for this case;
    - `acks_late=True` for at-least-once delivery — worker crash causes redelivery, idempotency handles duplicates;
    - 2-tier error taxonomy: operational errors (broker/DB down → retry) / application errors (invalid state → fail);

## Development & Testing
- Single `docker-compose.yml` for dev and test — test isolation via hash-suffixed DB and queue names;
- pytest with integration tests against real RabbitMQ — no eager-mode shortcuts;









# Additional Ideas for Tutorial
- Celery Beat for periodic task execution:
    - delete expired verification tokens;
- Task result tracking with django-celery-results and a task status polling endpoint:
    ? other use cases, which rely on DCR's table (restarting failed tasks, storing idempotency keys, ???);
- Canvas primitives: chain, group, chord for task workflows;
- Task priority queues;
