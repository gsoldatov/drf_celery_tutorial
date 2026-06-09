# Overview
A tutorial project, which focuses on use cases for Celery tasks within a Django Rest Framework application.


# Key Implemented Features
- [x] custom user model & endpoints for it (user registration & fetch, email verifiction)
- [x] Celery task for "sending" a verification email with retries, failure handling and idempotency;
- [x] Celery Beat task for periodic clean up of expired email verification tokens.


# Stack
- `Python 3.13`;
- `Docker Compose`;
- `Django Rest Framework`;
- `PostgreSQL 17`;
- `Celery` + `Celery Beat`;
- `RabbitMQ`;
- `pytest-django`.


# How to Set up Project and Run Development Server
Prerequisites:
- Python 3.13
- Docker Compose

```bash
# 1. Create and edit .env file
cp .env.example .env

# 2. Venv & dependencies
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start PostgreSQL & RabbitMQ
docker compose up -d

# 4. Apply migrations
python src/manage.py migrate

# 4.1. Create superuser (optional)
python src/manage.py createsuperuser

# 5. Run development server
python src/manage.py runserver

# 5.1. Run Celery worker & beat (in a separate terminal)
cd src
celery -A api worker --loglevel=info -B
# # (for Celery 5.6 & RabbitMQ 4.3+ additional args are required to fix errors caused by using transient non-exclusive queues;
# # this should also be paired with additional configuration in settings.py and Celery test fixtures;
# # this is skipped in favor of downgrading to RabbitMQ 4.2)
# celery -A api worker --loglevel=info --without-mingle --without-gossip
```


# How to Run Tests
Before running tests, steps 1-3 from the previous section must be completed (.env file, project venv, Docker containers).

```bash
# Run all tests
pytest
```
