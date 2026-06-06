# Implementation Plan
+ plan architecture;
- drf:
    - set up project:
        - venv, dependencies & django initialization;
        - .env file config -> loading & validation;
    - set up orm schemas & db migrations:
        - user (id, name, registered_at, status (pending_activation, active, disabled));
        - user_activation_tokens (id, user_id, token, expires_at);
    - set up route handlers without celery:
        - user registration (validate -> add a user to the database -> register a task on commit (later, when celery is added));
        - get an existing user;
        - activate user account (get token from URL -> check if it exists -> change status of a corresponding user);
    - add dockerfile for drf;
    - add docker-compose.yml:
        - drf;
        - postgresql;
    - add tests:
        - use pytest;
        - fixtures:
            - project config, updated with test configuration;
            - test db setup & teardown;
            - test client;
            ? other;
        - test cases:
            - config parsing;
            - db migrations;
            - endpoints;

- configure celery:
    - add celery & rabbitmq to docker-compose.yml;
    - update prjoect config -> configure celery & rabbitmq;
    - add email task:
        - add a task function;
        - ensure task idempotency;
        - configure task retries;
        - configure at least once delivery;

    - add a worker to docker-compose.yml;

    - add integration tests for celery tasks:
        - update fixtures:
            - test rabbitmq queue setup & teardown;
            ? other;
        - test cases:
            ? new endpoints;
            ? new migrations;
            - integration cases for tasks:
                - successful task;
                - idempotency;
                - failure & retry:
                    - operational errors (broker or DB down);
                    - application errors (user already activated, ???)
                    ? monkeypatch task or a function called inside it to simulate failures

- add a script / functions for setting up dev environment (running migrations, etc.);
- add readme;


# Key Architecture Decisions
- Token-based idempotency over django-celery-results for task outcome tracking;
- Separate `user_activation_tokens` table — non-user data and token lifecycle are independent;
- `transaction.on_commit()` for task dispatch — avoids worker racing the DB commit;
- `acks_late=True` for at-least-once delivery — worker crash causes redelivery, idempotency handles duplicates;
- 2-tier error taxonomy: operational errors (broker/DB down → retry) / application errors (invalid state → fail);
- Single `docker-compose.yml` for dev and test — test isolation via hash-suffixed DB and queue names;
- pytest with integration tests against real RabbitMQ — no eager-mode shortcuts;
- No authentication — API is open;

# Additional Ideas for Tutorial
- Task result tracking with django-celery-results and a task status polling endpoint:
    ? other use cases, which rely on DCR's table (restarting failed tasks, storing idempotency keys, ???);
- Celery Beat for periodic task execution;
- Canvas primitives: chain, group, chord for task workflows;
- Task priority queues;
