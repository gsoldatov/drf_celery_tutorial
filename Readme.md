# Overview
A tutorial project, which focuses on use cases for Celery tasks within a Django Rest Framework application.

Current plan:
- [x] scaffold project (DRF + PostgreSQL)
- [x] add custom user model & endpoints for it (user registration & fetch, email verifiction)
- [ ] set up Celery with RabbitMQ as a broker
- [ ] add a Celery task for "sending" a verification email
- [ ] add a Celery task for periodic clean up of expired verification tokens
