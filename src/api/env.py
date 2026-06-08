from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured


def validate_env(env=None):
    if env is None:
        env = environ.Env()
        env.read_env(Path(__file__).resolve().parents[2] / ".env")

    config = {}

    config["SECRET_KEY"] = env.str("SECRET_KEY")
    if len(config["SECRET_KEY"]) < 50:
        raise ImproperlyConfigured(
            "SECRET_KEY must be at least 50 characters long."
        )

    config["DEBUG"] = env.bool("DEBUG")

    config["ALLOWED_HOSTS"] = env.list("ALLOWED_HOSTS")
    if not config["ALLOWED_HOSTS"]:
        raise ImproperlyConfigured(
            "ALLOWED_HOSTS must be a non-empty list."
        )

    config["POSTGRES_HOST"] = env.str("POSTGRES_HOST")
    if not config["POSTGRES_HOST"]:
        raise ImproperlyConfigured(
            "POSTGRES_HOST must be a non-empty string."
        )

    try:
        config["POSTGRES_PORT"] = env.int("POSTGRES_PORT")
    except ValueError:
        raise ImproperlyConfigured(
            "POSTGRES_PORT must be a valid integer."
        )
    if not (1 <= config["POSTGRES_PORT"] <= 65535):
        raise ImproperlyConfigured(
            f"POSTGRES_PORT must be between 1 and 65535, "
            f"got {config['POSTGRES_PORT']}."
        )

    config["POSTGRES_DB"] = env.str("POSTGRES_DB")
    if not config["POSTGRES_DB"]:
        raise ImproperlyConfigured(
            "POSTGRES_DB must be a non-empty string."
        )

    config["POSTGRES_USER"] = env.str("POSTGRES_USER")
    if not config["POSTGRES_USER"]:
        raise ImproperlyConfigured(
            "POSTGRES_USER must be a non-empty string."
        )

    config["POSTGRES_PASSWORD"] = env.str("POSTGRES_PASSWORD")
    if not config["POSTGRES_PASSWORD"]:
        raise ImproperlyConfigured(
            "POSTGRES_PASSWORD must be a non-empty string."
        )

    config["CELERY_BROKER_HOST"] = env.str("CELERY_BROKER_HOST")
    if not config["CELERY_BROKER_HOST"]:
        raise ImproperlyConfigured(
            "CELERY_BROKER_HOST must be a non-empty string."
        )

    try:
        config["CELERY_BROKER_PORT"] = env.int("CELERY_BROKER_PORT")
    except ValueError:
        raise ImproperlyConfigured(
            "CELERY_BROKER_PORT must be a valid integer."
        )
    if not (1 <= config["CELERY_BROKER_PORT"] <= 65535):
        raise ImproperlyConfigured(
            f"CELERY_BROKER_PORT must be between 1 and 65535, "
            f"got {config['CELERY_BROKER_PORT']}."
        )

    try:
        config["CELERY_BROKER_MANAGEMENT_PORT"] = env.int(
            "CELERY_BROKER_MANAGEMENT_PORT"
        )
    except ValueError:
        raise ImproperlyConfigured(
            "CELERY_BROKER_MANAGEMENT_PORT must be a valid integer."
        )
    if not (1 <= config["CELERY_BROKER_MANAGEMENT_PORT"] <= 65535):
        raise ImproperlyConfigured(
            f"CELERY_BROKER_MANAGEMENT_PORT must be between 1 and 65535, "
            f"got {config['CELERY_BROKER_MANAGEMENT_PORT']}."
        )

    config["CELERY_TASK_DEFAULT_QUEUE"] = env.str("CELERY_TASK_DEFAULT_QUEUE")
    if not config["CELERY_TASK_DEFAULT_QUEUE"]:
        raise ImproperlyConfigured(
            "CELERY_TASK_DEFAULT_QUEUE must be a non-empty string."
        )

    try:
        config["EMAIL_VERIFICATION_TOKEN_LIFETIME"] = env.int(
            "EMAIL_VERIFICATION_TOKEN_LIFETIME"
        )
    except ValueError:
        raise ImproperlyConfigured(
            "EMAIL_VERIFICATION_TOKEN_LIFETIME must be a valid integer."
        )
    if config["EMAIL_VERIFICATION_TOKEN_LIFETIME"] <= 0:
        raise ImproperlyConfigured(
            f"EMAIL_VERIFICATION_TOKEN_LIFETIME must be a positive integer, "
            f"got {config['EMAIL_VERIFICATION_TOKEN_LIFETIME']}."
        )

    return config
