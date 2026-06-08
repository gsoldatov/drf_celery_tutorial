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
                + database network errors;
    
    + validate .env file, when loading:
        + add validation tests;
    + rename artifacts related to email_verified field to match its name;

- configure celery:
    + add rabbitmq to docker-compose.yml;
    + update prjoect config -> configure celery & rabbitmq;
    - add email task:
        + add a task function;
        - ensure task idempotency;
        + configure task retries;
        + configure at least once delivery;

    x add a worker to docker-compose.yml;   // local process is used instead

    - add integration tests for celery tasks:
        + update fixtures:
            + test rabbitmq queue setup & teardown;
        - test cases:
            - integration cases for tasks:
                + successful task:
                    + send_email receives correct email and token;
                    + token state & send time updated after email is "sent";
                - errors:
                    - broker down:
                        - view returns correct response;
                        - task creation error is handled gracefully;
                    - DB down:
                        - before email is "sent":
                            - task is failed are retried:
                                - temporary failure -> task is retried and succeds;
                                - constant failure -> task is failed and db is not updated;
                        - after email is "sent":
                            - task is considered complete;  // email is not sent twice
                    - email "sending" failure:
                        - task is failed and retried:
                            - temporary failure -> task is retried and succeeds;
                            - constant failure -> task is failed;
                - idempotency:
                    - if multiple tasks are fired for the same token, email is sent only once:
                        - 2 tasks simultaneously receive the same token;
                        - second task starts after first completes;


- add admin user & test the full setup manually;
? add admin user to config;
? add a script / functions for setting up dev environment (running migrations, etc.);
- add readme;


# Key Architecture Decisions
## App & Celery General
- views with multiple database operations should wrap them in a single transaction;
- no auth restrictions for views;
- Celery tasks are dispatched via `transaction.on_commit()`;


## Development & Testing
- Single `docker-compose.yml` for dev and test — test isolation via hash-suffixed DB and queue names;
- pytest with integration tests against real RabbitMQ — no eager-mode shortcuts;


## Celery Cases
### Email "Sending" Task
- working with an override of auth.user model;
- `email_verification_tokens` table stored email validation tokens;
- not using django-celery-results, since it's redundant for this case;
- `acks_late=True` for at-least-once delivery — worker crash causes redelivery, idempotency handles duplicates;


# Additional Ideas for Tutorial
- Celery Beat for periodic task execution:
    - delete expired verification tokens;
- Dead letter queue (failed email sends);
- Task result tracking with django-celery-results and a task status polling endpoint:
    ? other use cases, which rely on DCR's table (restarting failed tasks, storing idempotency keys, ???);
- Canvas primitives: chain, group, chord for task workflows;
- Task priority queues;
