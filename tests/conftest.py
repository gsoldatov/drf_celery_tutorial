import pytest
from django.db import connections
from kombu import Connection, Queue
from rest_framework.test import APIClient
from users.models import User
from tests.util import get_free_port


# Test client
@pytest.fixture
def api_client():
    return APIClient()


# DB fixtures
@pytest.fixture
def db_unavailable():
    """Temporarily point DATABASES at a dead port so DB operations fail with OperationalError."""
    free_port = get_free_port()
    default_conn = connections["default"]
    original_port = default_conn.settings_dict["PORT"]
    default_conn.settings_dict["PORT"] = str(free_port)
    default_conn.close()
    try:
        yield
    finally:
        default_conn.settings_dict["PORT"] = original_port
        default_conn.close()


@pytest.fixture
def broker_unavailable():
    """Temporarily point Celery at a dead broker so .delay() raises OperationalError."""
    from django.conf import settings as django_settings
    from api.celery import app

    free_port = get_free_port()
    original = django_settings.CELERY_BROKER_URL
    django_settings.CELERY_BROKER_URL = f"amqp://localhost:{free_port}//"
    app.config_from_object("django.conf:settings", namespace="CELERY")
    try:
        yield
    finally:
        django_settings.CELERY_BROKER_URL = original
        app.config_from_object("django.conf:settings", namespace="CELERY")


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
    """Declare the test queue and purge it."""
    from api.celery import app

    with Connection(app.conf.broker_url) as conn:
        Queue(TEST_QUEUE)(conn.channel()).purge()


@pytest.fixture(scope="session")
def celery_test_queue():
    """Configure Celery to use a dedicated test queue (session-scoped, once per run).

    Overrides CELERY_TASK_DEFAULT_QUEUE at the Django settings level because
    app.conf.update() cannot change task_default_queue after config_from_object()
    has loaded it.
    """
    from django.conf import settings as django_settings
    from api.celery import app

    # Override at the Django settings level so Celery picks it up.
    django_settings.CELERY_TASK_DEFAULT_QUEUE = TEST_QUEUE
    app.config_from_object("django.conf:settings", namespace="CELERY")

    app.conf.update(
        task_always_eager=False,
        task_queues=[Queue(TEST_QUEUE)]
    )


@pytest.fixture
def purge_test_queue(celery_test_queue):
    """Purge the test queue before and after each test — safe on failures."""
    _purge_test_queue()
    try:
        yield
    finally:
        _purge_test_queue()


@pytest.fixture(scope="session")
def celery_worker(celery_test_queue):
    """Start a Celery worker in a background thread, consuming the test queue through
    RabbitMQ (session-scoped — started once per test run).

    Uses start_worker with pool='solo' (single-threaded, in-process) instead of
    task_always_eager=True because eager mode bypasses the broker entirely.
    This gives a true end-to-end path: view → broker → worker.
    """
    from celery.contrib.testing.worker import start_worker
    from api.celery import app

    try:
        with start_worker(
            app,
            pool="solo",             # single-threaded, in-process — no child workers
            queues=[TEST_QUEUE],     # only consume from the isolated test queue
            perform_ping_check=False,  # skip the startup ping round-trip
            shutdown_timeout=1.0,    # give the worker thread time to drain
        ) as worker:
            yield worker
    except RuntimeError:
        pass  # worker thread didn't unblock — daemon, killed with the process
    finally:
        app.pool.force_close_all()
