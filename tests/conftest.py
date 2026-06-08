import pytest
from kombu import Connection, Queue
from rest_framework.test import APIClient
from users.models import User


# Test client
@pytest.fixture
def api_client():
    return APIClient()


# DB data fixtures
@pytest.fixture
def create_user(db):
    def _create_user(**kwargs):
        defaults = {
            "email": "test@example.com",
            "password": "secret123",
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    return _create_user


# Test RabbitMQ queue fixtures
TEST_QUEUE = "celery_test"


def _purge_test_queue():
    from api.celery import app

    with Connection(app.conf.broker_url) as conn:
        Queue(TEST_QUEUE)(conn.channel()).purge()


@pytest.fixture(scope="module")
def celery_test_queue():
    """Point Celery at a dedicated test queue (one-time setup per module)."""
    from api.celery import app

    app.conf.update(
        task_always_eager=False,
        task_default_queue=TEST_QUEUE,
    )


@pytest.fixture
def purge_test_queue(celery_test_queue):
    """Purge the test queue before and after each test — safe on failures."""
    _purge_test_queue()
    try:
        yield
    finally:
        _purge_test_queue()
